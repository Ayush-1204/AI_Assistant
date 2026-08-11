import os
import re

with open(r'apps\client\web\lib\chat_view.dart', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Rename _HoverableAttachmentPill
for i in range(len(lines)):
    lines[i] = lines[i].replace('_HoverableAttachmentPill', 'HoverableAttachmentPill')

# 2. Add Positioned.fill and AnimatedSize
start_pos_idx = -1
for i in range(len(lines)):
    if 'return Container(' in lines[i] and 'padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),' in lines[i+1] and i > 1200:
        start_pos_idx = i
        break

if start_pos_idx != -1:
    lines[start_pos_idx] = lines[start_pos_idx].replace('return Container(', 'return Positioned.fill(\n                child: Container(')
    
    # Now find the if (isEmpty) block to wrap with AnimatedSize
    for i in range(start_pos_idx, len(lines)):
        if 'if (isEmpty) ...[' in lines[i]:
            # Replace the block
            lines[i] = '''                          AnimatedSize(
                            duration: const Duration(milliseconds: 600),
                            curve: Curves.easeOutCubic,
                            child: SizedBox(
                              height: isEmpty ? null : 0,
                              child: AnimatedOpacity(
                                duration: const Duration(milliseconds: 400),
                                opacity: isEmpty ? 1.0 : 0.0,
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
'''
            break
            
    for i in range(start_pos_idx, len(lines)):
        if 'const SizedBox(height: 48),' in lines[i]:
            # Replace the closing block
            lines[i+1] = '''                                  ],
                                ),
                              ),
                            ),
                          ),\n'''
            break

# 3. Replace Chat Input Pill Container
pill_start_idx = -1
for i in range(start_pos_idx, len(lines)):
    if 'Container(' in lines[i] and 'constraints: const BoxConstraints(maxWidth: 800),' in lines[i+1]:
        pill_start_idx = i
        break

if pill_start_idx != -1:
    pill_end_idx = -1
    for i in range(pill_start_idx, len(lines)):
        if '                        ), // End Container' in lines[i]:
            pill_end_idx = i
            break
            
    if pill_end_idx != -1:
        replacement = '                        ChatInputPill(controller: _controller, onSend: () => _handleSend(_controller.text)),\n'
        lines = lines[:pill_start_idx] + [replacement] + lines[pill_end_idx+1:]

# 4. Fix closing tags for Positioned.fill
for i in range(len(lines)):
    if '              ); // End return Container' in lines[i]:
        lines[i] = '              )); // End return Positioned.fill\n'

# 5. Move Consumer outside Column and remove unnecessary consumer logic
for i in range(len(lines)):
    if '            }), // End Consumer' in lines[i]:
        lines[i] = '''            Consumer(builder: (context, ref, child) {
              final isListening = ref.watch(chatProvider).isListening;
              final isSending = ref.watch(chatProvider).isSending;
              final isProcessing = ref.watch(chatProvider).isProcessing;
              final isEmpty = ref.watch(chatProvider).messages.isEmpty;
              final isContinuousVoiceMode = ref.watch(chatProvider).isContinuousVoiceMode;
              return SizedBox.shrink(); // Logic moved
            }),
'''
        # We need to remove the start of Consumer which is now wrapped by Positioned.fill
        # But wait, we don't need to do that because the original Consumer was wrapping the Container.
        # Actually, if we just let it be, it's fine.

content = "".join(lines)
content = content.replace("import 'workspace_view.dart';", "import 'workspace_view.dart';\nimport 'widgets/chat_input_pill.dart';")

with open(r'apps\client\web\lib\chat_view.dart', 'w', encoding='utf-8') as f:
    f.write(content)

