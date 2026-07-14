import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter/foundation.dart';
import 'dart:async';
import 'dart:convert';
import 'package:audioplayers/audioplayers.dart';
import 'package:record/record.dart';
import '../api_client.dart';
import 'auth_provider.dart';

class ChatState {
  final int? conversationId;
  final List<String> messages;
  final bool isSending;
  final bool isListening;
  final bool isVoiceTyping;
  final String liveTranscript;
  final List<dynamic> sessions;
  final Map<int, Map<String, dynamic>> messageMetadata;
  final List<String> pendingImages;
  final double currentAmplitude;

  ChatState({
    this.conversationId,
    List<String>? messages,
    this.isSending = false,
    this.isListening = false,
    this.isVoiceTyping = false,
    this.liveTranscript = "",
    this.sessions = const [],
    this.messageMetadata = const {},
    this.pendingImages = const [],
    this.currentAmplitude = -160.0,
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
    List<String>? pendingImages,
    double? currentAmplitude,
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
      pendingImages: pendingImages ?? this.pendingImages,
      currentAmplitude: currentAmplitude ?? this.currentAmplitude,
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
  WebSocketChannel? _dictateChannel;
  StreamSubscription? _dictateStreamSub;
  String? _recordPath;
  final List<Uint8List> _audioQueue = [];
  bool _isPlayingAudio = false;
  final List<int> _voiceTypingBuffer = [];

  ChatNotifier(this._apiClient) : super(ChatState()) {
    _audioPlayer.onPlayerComplete.listen((_) {
      _isPlayingAudio = false;
      if (_audioQueue.isNotEmpty) {
        _processAudioQueue();
      }
    });
    _initializeConversation();
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

  Future<void> _cleanupGhostChat() async {
    if (state.conversationId != null && state.messages.length <= 1) {
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

    _initWebSocket();
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
      _initWebSocket();
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

  Future<void> _initWebSocket() async {
    if (state.conversationId == null) return;
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
          sampleRate: 48000,
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
       if (transcript.trim().isNotEmpty) {
          sendMessage(transcript.trim());
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
          sampleRate: 48000,
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

  Future<void> _processAudioQueue() async {
    if (_audioQueue.isEmpty) return;
    _isPlayingAudio = true;
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
      final cleanText = text.replaceAll(RegExp(r'\*|_|#'), '').trim();
      if (cleanText.isEmpty) return;
      final bytes = await _apiClient.textToSpeech(cleanText);
      await _playAudioBytes(bytes);
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
  
  void attachImage(String base64String) {
    state = state.copyWith(pendingImages: [...state.pendingImages, base64String]);
  }

  void clearAttachments() {
    state = state.copyWith(pendingImages: []);
  }

  void addMessage(String text) {
    state = state.copyWith(messages: [...state.messages, text]);
  }

  Future<void> sendMessage(String text, {bool isRegenerate = false}) async {
    if (text.trim().isEmpty || state.isSending) return;
    
    // Capture and clear immediately to prevent double sending
    final imagesToSend = List<String>.from(state.pendingImages);
    clearAttachments();
    
    addMessage(text.trim());
    state = state.copyWith(isSending: true);
    
    try {
      if (state.conversationId == null) {
         final newId = await _apiClient.createConversation("New Chat");
         state = state.copyWith(conversationId: newId);
         _initWebSocket();
      }
      
      final replyData = await _apiClient.sendChatMessage(
        state.conversationId.toString(), 
        text, 
        isRegenerate: isRegenerate,
        images: imagesToSend,
      );
      String assistantReply = replyData['response'] ?? '';
      addMessage("Assistant: $assistantReply");
      
      // Auto-edit title on first user/assistant exchange
      if (state.messages.length <= 3) {
        String cleaned = assistantReply.replaceAll(RegExp(r'\n|#|\*'), ' ').trim();
        String newTitle = cleaned.length > 25 ? "${cleaned.substring(0, 25).trim()}..." : cleaned;
        if (newTitle.isNotEmpty) {
           await updateChatTitle(state.conversationId!, newTitle);
        }
      }
      
      if (replyData['metadata'] != null) {
        final newMeta = Map<int, Map<String, dynamic>>.from(state.messageMetadata);
        newMeta[state.messages.length - 1] = replyData['metadata'] as Map<String, dynamic>;
        state = state.copyWith(messageMetadata: newMeta);
      }
    } catch (e) {
      addMessage("Assistant: Error connecting to backend: $e");
    } finally {
      state = state.copyWith(isSending: false);
    }
  }

  @override
  void dispose() {
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
