import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'auth_provider.dart';
import '../models/conversation_info.dart';

final chatHistoryProvider = FutureProvider<List<ConversationInfo>>((ref) async {
  final client = ref.read(apiClientProvider);
  return await client.fetchConversations();
});

