import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter/foundation.dart';
import '../api_client.dart';
import 'auth_provider.dart';

class ChatState {
  final int? conversationId;
  final List<String> messages;
  final bool isSending;
  final bool isListening;
  final List<dynamic> sessions;

  ChatState({
    this.conversationId,
    this.messages = const [
      "Assistant: Hello! I am your Second Brain. I can access your notes, fetch files, manage your calendar, or search the web.\n\n*How can I assist you today?*"
    ],
    this.isSending = false,
    this.isListening = false,
    this.sessions = const [],
  });

  ChatState copyWith({
    int? conversationId,
    List<String>? messages,
    bool? isSending,
    bool? isListening,
    List<dynamic>? sessions,
  }) {
    return ChatState(
      conversationId: conversationId ?? this.conversationId,
      messages: messages ?? this.messages,
      isSending: isSending ?? this.isSending,
      isListening: isListening ?? this.isListening,
      sessions: sessions ?? this.sessions,
    );
  }
}

class ChatNotifier extends StateNotifier<ChatState> {
  final ApiClient _apiClient;
  WebSocketChannel? _channel;

  ChatNotifier(this._apiClient) : super(ChatState()) {
    _initializeConversation();
  }

  Future<void> _initializeConversation() async {
    try {
      final conversations = await _apiClient.fetchConversations();
      if (conversations.isNotEmpty) {
        state = state.copyWith(
          conversationId: conversations.first['id'] as int,
          sessions: conversations,
        );
        _initWebSocket();
      } else {
        state = state.copyWith(sessions: []);
      }
    } catch (e) {
      debugPrint("Failed to load conversation: $e");
    }
  }

  Future<void> switchSession(int id) async {
    state = state.copyWith(
       conversationId: id,
       messages: ["Assistant: Loading conversation history..."],
    );
    _initWebSocket();
  }

  Future<void> _initWebSocket() async {
    if (state.conversationId == null) return;
    try {
      _channel = _apiClient.connectToVoiceStream(state.conversationId.toString());
      await _channel?.ready;
    } catch (e) {
      debugPrint("WebSocket init failed: $e");
    }
  }

  WebSocketChannel? get channel => _channel;
  
  void toggleListening() {
    state = state.copyWith(isListening: !state.isListening);
    if (state.isListening) {
      _channel?.sink.add("START_AUDIO_STREAM");
    } else {
      _channel?.sink.add("STOP_AUDIO_STREAM");
    }
  }
  
  void addMessage(String text) {
    state = state.copyWith(messages: [...state.messages, text]);
  }

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty || state.isSending) return;
    
    addMessage(text.trim());
    state = state.copyWith(isSending: true);
    
    try {
      if (state.conversationId == null) {
         final newId = await _apiClient.createConversation("New Chat");
         state = state.copyWith(conversationId: newId);
         _initWebSocket();
      }
      
      final reply = await _apiClient.sendChatMessage(state.conversationId.toString(), text);
      addMessage("Assistant: $reply");
    } catch (e) {
      addMessage("Assistant: Error connecting to backend: $e");
    } finally {
      state = state.copyWith(isSending: false);
    }
  }

  @override
  void dispose() {
    _channel?.sink.close();
    super.dispose();
  }
}

final chatProvider = StateNotifierProvider<ChatNotifier, ChatState>((ref) {
  final api = ref.watch(apiClientProvider);
  return ChatNotifier(api);
});
