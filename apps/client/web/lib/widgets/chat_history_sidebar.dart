import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/chat_history_provider.dart';
import '../providers/chat_provider.dart';
import '../models/conversation_info.dart';

class ChatHistorySidebar extends ConsumerWidget {
  const ChatHistorySidebar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(chatHistoryProvider);
    final activeConvId = ref.watch(chatProvider).conversationId;

    return Container(
      width: 280,
      decoration: const BoxDecoration(
        color: Color(0xFF131313),
        border: Border(
          right: BorderSide(
            color: Colors.white10,
            width: 1,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Conversations',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.add, color: Colors.white),
                  onPressed: () {
                    ref.read(chatProvider.notifier).startNewChat();
                  },
                )
              ],
            ),
          ),
          Expanded(
            child: historyAsync.when(
              data: (conversations) {
                if (conversations.isEmpty) {
                  return const Center(
                    child: Text('No conversations yet', style: TextStyle(color: Colors.white60)),
                  );
                }

                final pinned = conversations.where((c) => c.isPinned).toList();
                final recent = conversations.where((c) => !c.isPinned).toList();

                return ListView(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  children: [
                    if (pinned.isNotEmpty) ...[
                      const Padding(
                        padding: EdgeInsets.fromLTRB(8, 16, 8, 8),
                        child: Text(
                          'Pinned',
                          style: TextStyle(color: Colors.white54, fontSize: 12, fontWeight: FontWeight.bold),
                        ),
                      ),
                      ...pinned.map((c) => _buildChatItem(context, ref, c, activeConvId)),
                    ],
                    if (recent.isNotEmpty) ...[
                      const Padding(
                        padding: EdgeInsets.fromLTRB(8, 16, 8, 8),
                        child: Text(
                          'Recent',
                          style: TextStyle(color: Colors.white54, fontSize: 12, fontWeight: FontWeight.bold),
                        ),
                      ),
                      ...recent.map((c) => _buildChatItem(context, ref, c, activeConvId)),
                    ]
                  ],
                );
              },
              loading: () => const Center(child: CircularProgressIndicator(color: Colors.white24)),
              error: (err, stack) => Center(child: Text('Failed to load: $err', style: const TextStyle(color: Colors.red))),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildChatItem(BuildContext context, WidgetRef ref, ConversationInfo conv, int? activeId) {
    final isActive = conv.id == activeId;
    return Container(
      margin: const EdgeInsets.only(bottom: 4),
      decoration: BoxDecoration(
        color: isActive ? Colors.white.withValues(alpha: 0.1) : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
      ),
      child: ListTile(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        title: Text(
          conv.title,
          style: TextStyle(
            color: isActive ? Colors.white : Colors.white70,
            fontSize: 14,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        onTap: () {
          ref.read(chatProvider.notifier).switchSession(conv.id);
        },
        hoverColor: Colors.white.withValues(alpha: 0.05),
      ),
    );
  }
}

