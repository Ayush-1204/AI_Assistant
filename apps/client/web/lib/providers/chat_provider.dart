import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter/foundation.dart';
import 'dart:async';
import 'dart:convert';
import 'package:audioplayers/audioplayers.dart';
import 'package:record/record.dart';
import '../api_client.dart';
import 'auth_provider.dart';

class PendingFile {
  final String name;
  final String type; // 'image', 'document'
  final Uint8List bytes;
  final String base64Data; // only populated if it's an image

  PendingFile({
    required this.name,
    required this.type,
    required this.bytes,
    this.base64Data = "",
  });
}

class ChatState {
  final int? conversationId;
  final List<String> messages;
  final bool isSending;
  final bool isListening;
  final bool isVoiceTyping;
  final String liveTranscript;
  final List<dynamic> sessions;
  final Map<int, Map<String, dynamic>> messageMetadata;
  final List<PendingFile> pendingFiles;
  final double currentAmplitude;
  final bool isSpeaking;
  final bool isContinuousVoiceMode;
  final bool isProcessing;
  final bool shouldAutoExitVoiceMode;
  final bool isVoiceModeExpanded;
  final String loadingText;
  final List<Map<String, dynamic>>? pendingPlan; // non-null when plan_approval is pending
  final int? pendingPlanMsgIndex;
  /// Live list of presentation nodes arriving over SSE, keyed by message index.
  /// Used to render nodes incrementally during streaming without re-parsing the full string.
  final Map<int, List<Map<String, dynamic>>> streamingNodes;

  ChatState({
    this.conversationId,
    List<String>? messages,
    this.isSending = false,
    this.isListening = false,
    this.isVoiceTyping = false,
    this.liveTranscript = "",
    this.sessions = const [],
    this.messageMetadata = const {},
    this.pendingFiles = const [],
    this.currentAmplitude = -160.0,
    this.isSpeaking = false,
    this.isContinuousVoiceMode = false,
    this.isProcessing = false,
    this.shouldAutoExitVoiceMode = false,
    this.isVoiceModeExpanded = false,
    this.loadingText = "Thinking...",
    this.pendingPlan,
    this.pendingPlanMsgIndex,
    this.streamingNodes = const {},
  }) : messages = messages ?? [];

  ChatState copyWith({
    int? conversationId,
    List<String>? messages,
    bool? isSending,
    bool? isListening,
    bool? isVoiceTyping,
    String? liveTranscript,
    List<dynamic>? sessions,
    Map<int, Map<String, dynamic>>? messageMetadata,
    List<PendingFile>? pendingFiles,
    double? currentAmplitude,
    bool? isSpeaking,
    bool? isContinuousVoiceMode,
    bool? isProcessing,
    bool? shouldAutoExitVoiceMode,
    bool? isVoiceModeExpanded,
    String? loadingText,
    List<Map<String, dynamic>>? pendingPlan,
    bool clearPendingPlan = false,
    int? pendingPlanMsgIndex,
    Map<int, List<Map<String, dynamic>>>? streamingNodes,
    bool clearStreamingNodes = false,
  }) {
    return ChatState(
      conversationId: conversationId ?? this.conversationId,
      messages: messages ?? this.messages,
      isSending: isSending ?? this.isSending,
      isListening: isListening ?? this.isListening,
      isVoiceTyping: isVoiceTyping ?? this.isVoiceTyping,
      liveTranscript: liveTranscript ?? this.liveTranscript,
      sessions: sessions ?? this.sessions,
      messageMetadata: messageMetadata ?? this.messageMetadata,
      pendingFiles: pendingFiles ?? this.pendingFiles,
      currentAmplitude: currentAmplitude ?? this.currentAmplitude,
      isSpeaking: isSpeaking ?? this.isSpeaking,
      isContinuousVoiceMode: isContinuousVoiceMode ?? this.isContinuousVoiceMode,
      isProcessing: isProcessing ?? this.isProcessing,
      shouldAutoExitVoiceMode: shouldAutoExitVoiceMode ?? this.shouldAutoExitVoiceMode,
      isVoiceModeExpanded: isVoiceModeExpanded ?? this.isVoiceModeExpanded,
      loadingText: loadingText ?? this.loadingText,
      pendingPlan: clearPendingPlan ? null : (pendingPlan ?? this.pendingPlan),
      pendingPlanMsgIndex: clearPendingPlan ? null : (pendingPlanMsgIndex ?? this.pendingPlanMsgIndex),
      streamingNodes: clearStreamingNodes ? {} : (streamingNodes ?? this.streamingNodes),
    );
  }
}

class ChatNotifier extends StateNotifier<ChatState> {
  final ApiClient _apiClient;
  WebSocketChannel? _channel;
  final AudioPlayer _audioPlayer = AudioPlayer();
  final AudioRecorder _audioRecorder = AudioRecorder();
  Timer? _silenceTimer;
  StreamSubscription? _ampSub;
  StreamSubscription? _voiceStreamSub;
  StreamSubscription? _wsStreamSub;
  Timer? _sessionsRefreshTimer;
  WebSocketChannel? _dictateChannel;
  StreamSubscription? _dictateStreamSub;
  String? _recordPath;
  final List<Uint8List> _audioQueue = [];
  bool _isPlayingAudio = false;
  final List<int> _voiceTypingBuffer = [];

  void Function(Uint8List, bool)? _onAudioChunk;

  Timer? _typewriterTimer;
  String _networkMessageBuffer = "";
  final Map<String, String> _networkNodeTextBuffers = {};
  final Map<String, String> _networkNodeCodeBuffers = {};
  int _visibleMessageLen = 0;
  final Map<String, int> _visibleNodeTextLen = {};
  final Map<String, int> _visibleNodeCodeLen = {};
  int _currentMsgIndex = -1;
  bool _streamIsActive = false;

  ChatNotifier(this._apiClient) : super(ChatState()) {
    _audioPlayer.onPlayerComplete.listen((_) {
      _isPlayingAudio = false;
      if (_audioQueue.isNotEmpty) {
        _processAudioQueue();
      } else {
        state = state.copyWith(isSpeaking: false);
        if (state.isContinuousVoiceMode) {
           if (state.shouldAutoExitVoiceMode) {
              // Wait for voice_view to pick this up, do not toggle voice typing back on.
           } else {
              toggleVoiceTyping(); // Auto-restart listening for conversational flow!
           }
        }
      }
    });
    _initializeConversation();
    _sessionsRefreshTimer = Timer.periodic(const Duration(seconds: 15), (_) {
      refreshSessions();
    });
  }

  void setVoiceModeExpanded(bool expanded) {
    if (state.isVoiceModeExpanded != expanded) {
      state = state.copyWith(isVoiceModeExpanded: expanded);
    }
  }

  Future<void> _initializeConversation() async {
    try {
      final conversations = await _apiClient.fetchConversations();
      if (conversations.isNotEmpty) {
        state = state.copyWith(
          conversationId: null, // Force empty state on startup
          sessions: conversations,
          messages: [],
        );
      } else {
        state = state.copyWith(sessions: [], messages: [], conversationId: null);
      }
    } catch (e) {
      debugPrint("Failed to load conversation: $e");
    }
  }

  Future<void> refreshSessions() async {
    try {
      final conversations = await _apiClient.fetchConversations();
      state = state.copyWith(sessions: conversations);
    } catch (e) {
      debugPrint("Failed to refresh sessions: $e");
    }
  }

  Future<void> _cleanupGhostChat() async {
    if (state.conversationId != null && state.messages.isEmpty) {
      final oldId = state.conversationId!;
      try {
        await _apiClient.deleteConversation(oldId);
        final newSessions = state.sessions.where((s) => s['id'] != oldId).toList();
        state = state.copyWith(sessions: newSessions);
      } catch (e) {
        debugPrint("Ghost chat cleanup failed: $e");
      }
    }
  }

  Future<void> switchSession(int id) async {
    if (state.conversationId == id) return;
    
    await _cleanupGhostChat();

    state = state.copyWith(
       conversationId: id,
       messages: [],
    );
    
    final detail = await _apiClient.fetchConversation(id);
    if (detail.isNotEmpty && detail.containsKey('messages')) {
      final List<dynamic> msgData = detail['messages'];
      final parsed = msgData.map((m) {
         final role = m['role'] == 'user' ? 'User' : 'Assistant';
         return "$role: ${m['content']}";
      }).toList();
      
      state = state.copyWith(messages: parsed);
    } else {
      state = state.copyWith(messages: []);
    }
    
    if (state.isContinuousVoiceMode) {
      _initWebSocket();
    }
  }

  Future<void> startNewChat() async {
    await _cleanupGhostChat();
    
    state = state.copyWith(isSending: true);
    try {
      final newId = await _apiClient.createConversation("New Chat");
      
      final Map<String, dynamic> newSession = {
        'id': newId,
        'title': 'New Chat',
      };
      
      final updatedSessions = [newSession, ...state.sessions];
      
      state = ChatState(
        conversationId: newId,
        sessions: updatedSessions,
        messageMetadata: const {},
        messages: [],
      );
      
      _wsStreamSub?.cancel();
      _channel?.sink.close();
      _channel = null;
      if (state.isContinuousVoiceMode) {
        _initWebSocket();
      }
    } catch (e) {
      debugPrint("Failed to create new chat: $e");
    } finally {
      state = state.copyWith(isSending: false);
    }
  }

  Future<void> deleteChat(int id) async {
    try {
      await _apiClient.deleteConversation(id);
      final newSessions = state.sessions.where((s) => s['id'] != id).toList();
      state = state.copyWith(sessions: newSessions);
      if (state.conversationId == id) {
         if (newSessions.isNotEmpty) {
           await switchSession(newSessions.first['id'] as int);
         } else {
           await startNewChat();
         }
      }
    } catch (e) {
      debugPrint("Failed to delete chat: $e");
    }
  }

  Future<void> updateChatTitle(int id, String newTitle) async {
    try {
      await _apiClient.updateConversationTitle(id, newTitle);
      final newSessions = state.sessions.map((s) {
        if (s['id'] == id) {
          final copy = Map<String, dynamic>.from(s as Map<String, dynamic>);
          copy['title'] = newTitle;
          return copy;
        }
        return s;
      }).toList();
      state = state.copyWith(sessions: newSessions);
    } catch (e) {
      debugPrint("Failed to update title: $e");
    }
  }

  Future<void> pinChat(int id, bool pin) async {
    try {
      await _apiClient.updateConversationPin(id, pin);
      final newSessions = state.sessions.map((s) {
        if (s['id'] == id) {
          final copy = Map<String, dynamic>.from(s as Map<String, dynamic>);
          copy['is_pinned'] = pin;
          return copy;
        }
        return s;
      }).toList();
      state = state.copyWith(sessions: newSessions);
    } catch (e) {
      debugPrint("Failed to pin chat: $e");
    }
  }

  void resetVoiceExit() {
     state = state.copyWith(shouldAutoExitVoiceMode: false);
  }

  Future<void> _initWebSocket() async {
    if (state.conversationId == null) return;
    if (!state.isContinuousVoiceMode) return;
    
    try {
      _wsStreamSub?.cancel();
      _channel = _apiClient.connectToVoiceStream(state.conversationId.toString());
      await _channel?.ready;
      
      _wsStreamSub = _channel?.stream.listen((message) {
        if (message is String) {
          try {
            final data = jsonDecode(message);
            if (data['type'] == 'stt') {
               state = state.copyWith(liveTranscript: data['text'] as String);
            } else if (data['type'] == 'stt_agent_clear') {
               state = state.copyWith(liveTranscript: data['text'] as String);
            } else if (data['type'] == 'stt_agent') {
               state = state.copyWith(liveTranscript: state.liveTranscript + (data['text'] as String));
            }
          } catch (_) {}
        } else if (message is Uint8List) {
          _playAudioBytes(message);
        }
      });
    } catch (e) {
      debugPrint("WebSocket init failed: $e");
    }
  }

  WebSocketChannel? get channel => _channel;
  
  Future<void> stopListening() async {
     if (state.isListening) {
        _voiceStreamSub?.cancel();
        _ampSub?.cancel();
        await _audioRecorder.stop();
        state = state.copyWith(isListening: false, liveTranscript: "", currentAmplitude: -160.0);
     }
     if (state.isVoiceTyping) {
        await _stopVoiceTypingProcess();
     }
  }

  Future<void> toggleListening() async {
    if (state.isListening) {
      _voiceStreamSub?.cancel();
      _ampSub?.cancel();
      await _audioRecorder.stop();
      state = state.copyWith(isListening: false, liveTranscript: "", currentAmplitude: -160.0);
    } else {
      if (await _audioRecorder.hasPermission()) {
        // Use pcm16bits encoder — universally supported on Windows, Web, Android, iOS.
        final stream = await _audioRecorder.startStream(const RecordConfig(
          encoder: AudioEncoder.pcm16bits,
          sampleRate: 16000,
          numChannels: 1,
          echoCancel: true,
          autoGain: true,
          noiseSuppress: true,
        ));
        
        state = state.copyWith(isListening: true, liveTranscript: "Listening...");
        _voiceStreamSub = stream.listen((data) {
          if (state.isListening && _channel != null) {
            _channel!.sink.add(data);
          }
          _onAudioChunk?.call(data, false);
        });
        
        _ampSub = _audioRecorder.onAmplitudeChanged(const Duration(milliseconds: 50)).listen((amp) {
           if (state.isListening) {
             state = state.copyWith(currentAmplitude: amp.current);
           }
        });
      }
    }
  }

  Future<void> _stopVoiceTypingProcess() async {
    if (!state.isVoiceTyping) return;
    _ampSub?.cancel();
    _silenceTimer?.cancel();
    _silenceTimer = null;
    
    state = state.copyWith(liveTranscript: "Transcribing...");
    
    _voiceStreamSub?.cancel();
    await _audioRecorder.stop();
    _dictateStreamSub?.cancel();
    _dictateChannel?.sink.close();
    
    final payload = Uint8List.fromList(_voiceTypingBuffer);
    state = state.copyWith(isVoiceTyping: false, liveTranscript: "");
    
    if (payload.isNotEmpty) {
       final transcript = await _apiClient.transcribeAudio(payload);
       final cleanTranscript = transcript.trim();
       if (cleanTranscript.isNotEmpty && cleanTranscript != "." && cleanTranscript != "...") {
          sendMessage(cleanTranscript);
       }
    }
  }

  Future<void> toggleVoiceTyping() async {
    if (state.isVoiceTyping) {
      await _stopVoiceTypingProcess();
    } else {
      if (await _audioRecorder.hasPermission()) {
        // Use pcm16bits encoder — universally supported on Windows, Web, Android, iOS.
        final stream = await _audioRecorder.startStream(const RecordConfig(
          encoder: AudioEncoder.pcm16bits,
          sampleRate: 16000,
          numChannels: 1,
          echoCancel: true,
          autoGain: true,
          noiseSuppress: true,
        ));
        
        state = state.copyWith(isVoiceTyping: true, liveTranscript: "Listening...");
        _voiceTypingBuffer.clear();
        
        _voiceStreamSub = stream.listen((data) {
          if (state.isVoiceTyping) {
            _voiceTypingBuffer.addAll(data);
            _onAudioChunk?.call(data, false);
          }
        });
        
        _ampSub = _audioRecorder.onAmplitudeChanged(const Duration(milliseconds: 50)).listen((amp) {
           state = state.copyWith(currentAmplitude: amp.current);
           if (amp.current < -35.0) {
              if (_silenceTimer == null || !_silenceTimer!.isActive) {
                 _silenceTimer = Timer(const Duration(seconds: 3), () async {
                    if (state.isVoiceTyping) {
                       await _stopVoiceTypingProcess();
                    }
                 });
              }
           } else {
              _silenceTimer?.cancel();
              _silenceTimer = null;
           }
        });
      }
    }
  }
  
  /// Play raw audio bytes in a cross-platform way.
  /// On Flutter Web, audioplayers BytesSource does not support MP3 —
  /// encode as a data URI so UrlSource can handle it everywhere.
  Future<void> _playAudioBytes(Uint8List bytes) async {
    _audioQueue.add(bytes);
    if (!_isPlayingAudio) {
      _processAudioQueue();
    }
  }

  void setContinuousVoiceMode(bool val) {
    state = state.copyWith(
      isContinuousVoiceMode: val,
      isVoiceModeExpanded: val, // Automatically expand when mode is activated
    );
    if (!val) {
      if (state.isListening || state.isVoiceTyping) {
         stopListening();
      }
      _wsStreamSub?.cancel();
      _channel?.sink.close();
      _channel = null;
    } else {
      _initWebSocket();
    }
  }

  void setAudioChunkCallback(void Function(Uint8List, bool)? callback) {
    _onAudioChunk = callback;
  }

  Future<void> stopSpeaking() async {
    if (state.isSpeaking || _isPlayingAudio) {
      await _audioPlayer.stop();
      _isPlayingAudio = false;
      _audioQueue.clear();
      state = state.copyWith(isSpeaking: false);
      if (state.isContinuousVoiceMode && !(await _audioRecorder.isRecording())) {
         toggleVoiceTyping(); // resume listening if interrupted!
      }
    }
  }

  Future<void> _processAudioQueue() async {
    _isPlayingAudio = true;
    state = state.copyWith(isSpeaking: true); // Mute mic naturally occurs as toggleVoiceTyping is exited before TTS starts
    final bytes = _audioQueue.removeAt(0);
    
    await _audioPlayer.setVolume(1.0);
    if (kIsWeb) {
      final dataUri = Uri.dataFromBytes(bytes, mimeType: 'audio/wav').toString();
      await _audioPlayer.play(UrlSource(dataUri));
    } else {
      await _audioPlayer.play(BytesSource(bytes));
    }
  }

  Future<void> readAloud(String text) async {
    try {
      String extractText(String input) {
        String result = '';
        final lines = input.split('\n');
        for (final line in lines) {
          final trimmed = line.trim();
          if (trimmed.isEmpty) continue;
          if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
            try {
              final node = jsonDecode(trimmed);
              if (node is Map && node.containsKey('type')) {
                final type = node['type'];
                if (['Heading', 'Paragraph', 'Math', 'Code', 'Markdown'].contains(type)) {
                  result += (node['text']?.toString() ?? '') + ' ';
                } else if (type == 'Timeline') {
                  final events = node['events'] as List<dynamic>? ?? [];
                  for (final event in events) {
                    if (event is Map) {
                      result += '${event['time'] ?? ''}. ${event['title'] ?? ''}. ${event['description'] ?? ''} ';
                    }
                  }
                } else if (type == 'Accordion') {
                  result += '${node['title'] ?? ''}. ${node['content'] ?? ''} ';
                }
                // Skip structural widgets completely
                continue;
              }
            } catch (_) {}
          }
          result += line + ' ';
        }
        return result.replaceAll(RegExp(r'\*|_|#'), '').trim();
      }

      final cleanText = extractText(text);
      if (cleanText.isEmpty) return;

      final chunks = <String>[];
      String currentChunk = '';
      final words = cleanText.split(' ');
      for (final word in words) {
        currentChunk += word + ' ';
        if (currentChunk.trim().length > 15 && RegExp(r'[.!?\n]$').hasMatch(word)) {
          chunks.add(currentChunk.trim());
          currentChunk = '';
        }
      }
      if (currentChunk.trim().isNotEmpty) {
        chunks.add(currentChunk.trim());
      }

      for (final chunk in chunks) {
        if (chunk.isEmpty) continue;
        try {
          final bytes = await _apiClient.textToSpeech(chunk);
          await _playAudioBytes(bytes);
        } catch (e) {
          debugPrint("Chunk read aloud failed: $e");
        }
      }
    } catch (e) {
      debugPrint("Read aloud failed: $e");
    }
  }

  Future<void> regenerateLastResponse() async {
    int lastUserIndex = state.messages.lastIndexWhere((msg) => !msg.startsWith("Assistant:"));
    if (lastUserIndex == -1 || state.isSending) return;
    
    String userMsg = state.messages[lastUserIndex];
    final newMessages = state.messages.sublist(0, lastUserIndex);
    state = state.copyWith(messages: newMessages);
    await sendMessage(userMsg, isRegenerate: true);
  }
  
  void attachFile(PendingFile file) {
    state = state.copyWith(pendingFiles: [...state.pendingFiles, file]);
  }

  void clearAttachments() {
    state = state.copyWith(pendingFiles: []);
  }

   void _startTypewriterIfNeeded() {
      if (_typewriterTimer != null && _typewriterTimer!.isActive) return;
      _typewriterTimer = Timer.periodic(const Duration(milliseconds: 16), (timer) {
          bool didUpdate = false;
          final newMsgs = List<String>.from(state.messages);
          final currentNodes = List<Map<String, dynamic>>.from(state.streamingNodes[_currentMsgIndex] ?? []);
          
          // 1. Advance global message buffer (used for raw content, but not JSON structure)
          // (Wait, _networkMessageBuffer is also used for presentation_node json. We only want to animate if we are NOT in structured mode. If currentNodes is empty, we animate global message)
          if (currentNodes.isEmpty && _visibleMessageLen < _networkMessageBuffer.length) {
              _visibleMessageLen = (_visibleMessageLen + 3).clamp(0, _networkMessageBuffer.length);
              if (_currentMsgIndex >= 0 && _currentMsgIndex < newMsgs.length) {
                  newMsgs[_currentMsgIndex] = "Assistant: " + _networkMessageBuffer.substring(0, _visibleMessageLen);
              }
              didUpdate = true;
          }
          
          // 2. Advance node text buffers
          for (int i = 0; i < currentNodes.length; i++) {
              final node = Map<String, dynamic>.from(currentNodes[i]);
              final id = node['id'] as String;
              
              if (_networkNodeTextBuffers.containsKey(id)) {
                  final targetLen = _networkNodeTextBuffers[id]!.length;
                  final currentLen = _visibleNodeTextLen[id] ?? 0;
                  if (currentLen < targetLen) {
                      final remaining = targetLen - currentLen;
                      final step = (remaining * 0.3).ceil().clamp(1, 15);
                      _visibleNodeTextLen[id] = (currentLen + step).clamp(0, targetLen);
                      node['text'] = _networkNodeTextBuffers[id]!.substring(0, _visibleNodeTextLen[id]!);
                      currentNodes[i] = node;
                      didUpdate = true;
                  }
              }
              
              if (_networkNodeCodeBuffers.containsKey(id)) {
                  final targetLen = _networkNodeCodeBuffers[id]!.length;
                  final currentLen = _visibleNodeCodeLen[id] ?? 0;
                  if (currentLen < targetLen) {
                      _visibleNodeCodeLen[id] = (currentLen + 3).clamp(0, targetLen);
                      node['code'] = _networkNodeCodeBuffers[id]!.substring(0, _visibleNodeCodeLen[id]!);
                      currentNodes[i] = node;
                      didUpdate = true;
                  }
              }
          }
          
          if (didUpdate) {
              state = state.copyWith(
                  messages: newMsgs,
                  streamingNodes: currentNodes.isEmpty ? state.streamingNodes : {...state.streamingNodes, _currentMsgIndex: currentNodes},
              );
          } else if (!_streamIsActive) {
              timer.cancel();
          }
      });
   }
  void removeAttachment(int index) {
    if (index >= 0 && index < state.pendingFiles.length) {
      final updatedFiles = List<PendingFile>.from(state.pendingFiles)..removeAt(index);
      state = state.copyWith(pendingFiles: updatedFiles);
    }
  }

  void stopGenerating() {
    if (state.isProcessing) {
      _apiClient.abortChatStream();
      state = state.copyWith(isProcessing: false, loadingText: null);
    }
  }

  void cancelPlan() {
    state = state.copyWith(clearPendingPlan: true, isProcessing: false);
  }

  Future<void> approvePlan(List<Map<String, dynamic>> approvedSteps) async {
    if (state.conversationId == null) return;
    final planMsgIndex = state.pendingPlanMsgIndex;
    state = state.copyWith(clearPendingPlan: true, isProcessing: true, loadingText: 'Executing plan...');

    try {
      String accumulated = '';
      bool firstChunk = false;
      int msgIdx = planMsgIndex ?? state.messages.length;

      final stream = _apiClient.approvePlanStream(state.conversationId!, approvedSteps);
      await for (final payload in stream) {
        if (payload == '[DONE]') {
          state = state.copyWith(isProcessing: false);
          continue;
        }
        try {
          final data = jsonDecode(payload);
          if (data['type'] == 'content') {
            if (state.isProcessing) state = state.copyWith(isProcessing: false);
            if (!firstChunk) {
              firstChunk = true;
              final msgs = List<String>.from(state.messages);
              msgs.add('Assistant: ');
              msgIdx = msgs.length - 1;
              state = state.copyWith(messages: msgs);
            }
            accumulated += data['delta'] as String;
            final newMsgs = List<String>.from(state.messages);
            if (msgIdx < newMsgs.length) {
              newMsgs[msgIdx] = 'Assistant: $accumulated';
              state = state.copyWith(messages: newMsgs);
            }
          } else if (data['type'] == 'tool') {
            final name = data['name'] as String? ?? 'Executing...';
            state = state.copyWith(loadingText: name);
          }
        } catch (_) {}
      }
    } catch (e) {
      debugPrint('approvePlan error: $e');
    } finally {
      state = state.copyWith(isProcessing: false);
    }
  }

  void addMessage(String text) {
    state = state.copyWith(messages: [...state.messages, text]);
  }

  Future<void> editMessageAndSend(int index, String newText) async {
    if (state.conversationId == null) return;
    try {
      await _apiClient.truncateConversation(state.conversationId!, index);
    } catch (e) {
      debugPrint("Failed to truncate conversation: $e");
      return;
    }
    state = state.copyWith(messages: state.messages.sublist(0, index));
    await sendMessage(newText);
  }


  Future<void> sendMessage(String text, {bool isRegenerate = false}) async {
    if (text.trim().isEmpty || state.isSending) return;
    
    // Capture and clear immediately to prevent double sending
    final filesToSend = List<PendingFile>.from(state.pendingFiles);
    clearAttachments();
    
    String messageContent = text.trim();
    List<String> imageBase64s = [];
    
    if (filesToSend.isNotEmpty) {
      messageContent += "\n\n";
      for (final file in filesToSend) {
        if (file.type == 'image') {
          imageBase64s.add(file.base64Data);
          messageContent += "![attachment](data:image/jpeg;base64,${file.base64Data})\n";
        } else {
          try {
            // Upload non-image files (documents, pdfs, etc) to RAG backend
            await _apiClient.uploadDocument(file.name, file.bytes, file.name);
            messageContent += "[Attached Document: ${file.name} (Uploaded to Memory)]\n";
          } catch (e) {
            messageContent += "[Failed to upload document: ${file.name}]\n";
            debugPrint("Document upload failed: $e");
          }
        }
      }
    }
    
    addMessage(messageContent.trim());
    state = state.copyWith(isSending: true);
    
    final lower = text.toLowerCase();
    bool triggeredExit = ["bye", "goodbye", "see you soon", "talk to you later", "see ya", "exit voice"].any((p) => lower.contains(p));
    if (triggeredExit) {
        state = state.copyWith(shouldAutoExitVoiceMode: true);
    }
    
    try {
      if (state.conversationId == null) {
         final newId = await _apiClient.createConversation("New Chat");
         state = state.copyWith(conversationId: newId);
         refreshSessions(); // Ensure sidebar updates immediately
         if (state.isContinuousVoiceMode) {
           _initWebSocket();
         }
      }
      
      state = state.copyWith(isProcessing: true, loadingText: "Thinking...");
      
      _networkMessageBuffer = "";
      _networkNodeTextBuffers.clear();
      _networkNodeCodeBuffers.clear();
      _visibleMessageLen = 0;
      _visibleNodeTextLen.clear();
      _visibleNodeCodeLen.clear();
      _currentMsgIndex = -1;
      _streamIsActive = true;
      
      bool firstChunkReceived = false;
      
      final stream = _apiClient.sendChatMessageStream(
        state.conversationId.toString(), 
        messageContent.trim(), 
        isRegenerate: isRegenerate,
        images: imageBase64s,
      );
      
      await for (final payload in stream) {
         if (payload == "[DONE]") {
             _streamIsActive = false;
             state = state.copyWith(isProcessing: false);
             continue;
         }
         
         try {
           final data = jsonDecode(payload);
           if (data['type'] == 'content') {
              if (state.isProcessing) {
                  state = state.copyWith(isProcessing: false);
              }
              if (!firstChunkReceived) {
                  firstChunkReceived = true;
                  state = state.copyWith(messages: [...state.messages, "Assistant: "]);
                  _currentMsgIndex = state.messages.length - 1;
              }
              _networkMessageBuffer += data['delta'];
              _startTypewriterIfNeeded();
           } else if (data['type'] == 'metadata') {
              final newMeta = Map<int, Map<String, dynamic>>.from(state.messageMetadata);
              if (_currentMsgIndex >= 0) {
                  newMeta[_currentMsgIndex] = data;
                  state = state.copyWith(messageMetadata: newMeta);
              }
           } else if (data['type'] == 'node_start') {
              if (state.isProcessing) state = state.copyWith(isProcessing: false);
              if (!firstChunkReceived) {
                  firstChunkReceived = true;
                  state = state.copyWith(messages: [...state.messages, "Assistant: "]);
                  _currentMsgIndex = state.messages.length - 1;
              }
              final nodeId = data['id'] as String;
              final nodeType = data['node_type'] as String;
              final skelNode = <String, dynamic>{'id': nodeId, 'type': nodeType, 'text': '', 'code': ''};
              
              final currentNodes = List<Map<String, dynamic>>.from(state.streamingNodes[_currentMsgIndex] ?? []);
              currentNodes.add(skelNode);
              state = state.copyWith(streamingNodes: {...state.streamingNodes, _currentMsgIndex: currentNodes});
              
           } else if (data['type'] == 'node_text_delta') {
              final nodeId = data['id'] as String;
              final delta = data['delta'] as String;
              
              final currentNodes = List<Map<String, dynamic>>.from(state.streamingNodes[_currentMsgIndex] ?? []);
              final nodeIndex = currentNodes.indexWhere((n) => n['id'] == nodeId);
              if (nodeIndex >= 0) {
                 final node = Map<String, dynamic>.from(currentNodes[nodeIndex]);
                 if ((node['type'] as String).toLowerCase() == 'codeblock') {
                     _networkNodeCodeBuffers[nodeId] = (_networkNodeCodeBuffers[nodeId] ?? "") + delta;
                 } else {
                     _networkNodeTextBuffers[nodeId] = (_networkNodeTextBuffers[nodeId] ?? "") + delta;
                 }
                 _startTypewriterIfNeeded();
              }
              
           } else if (data['type'] == 'presentation_node') {
              if (state.isProcessing) {
                  state = state.copyWith(isProcessing: false);
              }
               if (!firstChunkReceived) {
                   firstChunkReceived = true;
                   state = state.copyWith(messages: [...state.messages, "Assistant: "]);
                   _currentMsgIndex = state.messages.length - 1;
               }
               final nodeMap = Map<String, dynamic>.from(data['node'] as Map);
               _networkMessageBuffer += jsonEncode(nodeMap) + "\n";

              // Update message string for persistence
              final newMsgs = List<String>.from(state.messages);
              if (_currentMsgIndex >= 0 && _currentMsgIndex < newMsgs.length) {
                  newMsgs[_currentMsgIndex] = "Assistant: " + _networkMessageBuffer;
              }
              
              // Update live node list: replace skeleton or append
              final currentNodes = List<Map<String, dynamic>>.from(state.streamingNodes[_currentMsgIndex] ?? []);
              final nodeId = nodeMap['id'];
              final existingIndex = currentNodes.indexWhere((n) => n['id'] == nodeId);
              if (existingIndex >= 0) {
                  currentNodes[existingIndex] = nodeMap;
              } else {
                  currentNodes.add(nodeMap);
              }
              
              state = state.copyWith(
                  messages: newMsgs,
                  streamingNodes: {...state.streamingNodes, _currentMsgIndex: currentNodes},
              );

              // Auto-compress voice mode to reveal widgets
              if (state.isVoiceModeExpanded) {
                  setVoiceModeExpanded(false);
              }
           } else if (data['type'] == 'tool') {
              final name = data['name'] as String? ?? 'Executing tools...';
              state = state.copyWith(loadingText: name.contains('Searching') ? 'Searching the web...' : name);
           } else if (data['type'] == 'plan_approval') {
              // Agent halted — surface the plan card in the UI
              final rawPlan = data['plan'] as List<dynamic>? ?? [];
              final typedPlan = rawPlan.map((s) => Map<String, dynamic>.from(s as Map)).toList();
              state = state.copyWith(
                isProcessing: false,
                pendingPlan: typedPlan,
                pendingPlanMsgIndex: _currentMsgIndex,
              );
           }
         } catch (_) {}
      }
      
      if (state.isContinuousVoiceMode && _networkMessageBuffer.trim().isNotEmpty) {
         readAloud(_networkMessageBuffer);
      }
      
      // Auto-edit title on first user/assistant exchange
      if (state.messages.length <= 3 && state.conversationId != null) {
        String cleaned = _networkMessageBuffer.replaceAll(RegExp(r'\n|#|\*'), ' ').trim();
        if (cleaned.isNotEmpty) {
           final newTitle = await _apiClient.generateConversationTitle(state.conversationId!, cleaned);
           if (newTitle != null && newTitle.isNotEmpty) {
              await updateChatTitle(state.conversationId!, newTitle);
           }
        }
      }
      
      state = state.copyWith(isProcessing: false);
    } catch (e) {
      // Don't modify messages if the user explicitly cancelled the stream, just drop the connection natively
      if (e.toString().contains('Connection closed') || e.toString().contains('Stream failed') || e.toString().contains('ClientException')) {
          state = state.copyWith(isProcessing: false, loadingText: null);
          return;
      }
      final newMsgs = List<String>.from(state.messages);
      if (newMsgs.isNotEmpty && newMsgs.last == "Assistant: ") {
        newMsgs.removeLast();
      }
      state = state.copyWith(
        isProcessing: false, 
        messages: newMsgs,
      );
    } finally {
      state = state.copyWith(isSending: false);
    }
  }

  @override
  void dispose() {
    _silenceTimer?.cancel();
    _sessionsRefreshTimer?.cancel();
    _ampSub?.cancel();
    _voiceStreamSub?.cancel();
    _wsStreamSub?.cancel();
    _dictateStreamSub?.cancel();
    _silenceTimer?.cancel();
    _channel?.sink.close();
    _dictateChannel?.sink.close();
    _audioPlayer.dispose();
    _audioRecorder.dispose();
    super.dispose();
  }
}

final chatProvider = StateNotifierProvider<ChatNotifier, ChatState>((ref) {
  final api = ref.watch(apiClientProvider);
  return ChatNotifier(api);
});
