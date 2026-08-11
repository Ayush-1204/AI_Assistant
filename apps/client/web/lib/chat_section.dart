import 'package:flutter/material.dart';
import 'chat_view.dart';
import 'widgets/chat_history_sidebar.dart';

class ChatSection extends StatelessWidget {
  const ChatSection({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const ChatHistorySidebar(),
        Expanded(
          child: const ChatView(),
        ),
      ],
    );
  }
}
