import os

with open(r'apps\client\web\lib\chat_view.dart', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update ListView padding
content = content.replace(
    'padding: const EdgeInsets.fromLTRB(0, 24, 0, 24),',
    'padding: const EdgeInsets.fromLTRB(0, 24, 0, 200),'
)

# 2. Add Positioned.fill
content = content.replace(
    '''              return Container(
                padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
                color: Colors.transparent,
                child: SafeArea(
                  child: AnimatedAlign(
                    duration: const Duration(milliseconds: 600),
                    curve: Curves.easeOutCubic,
                    alignment: isEmpty
                        ? const Alignment(0, 0)
                        : Alignment.bottomCenter,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (isEmpty) ...[
                          const Text("Greetings, Ayush",
                              style: TextStyle(
                                  fontSize: 32,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                  letterSpacing: -0.5)),
                          const SizedBox(height: 12),
                          Text("What's on your mind today?",
                              style: TextStyle(
                                  fontSize: 18,
                                  color: Colors.white.withValues(alpha: 0.6))),
                          const SizedBox(height: 48),
                        ],''',
    '''              return Positioned.fill(
                child: Container(
                  padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
                  color: Colors.transparent,
                  child: SafeArea(
                    child: AnimatedAlign(
                      duration: const Duration(milliseconds: 600),
                      curve: Curves.easeOutCubic,
                      alignment: isEmpty
                          ? const Alignment(0, 0)
                          : Alignment.bottomCenter,
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          AnimatedSize(
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
                                    const Text("Greetings, Ayush",
                                        style: TextStyle(
                                            fontSize: 32,
                                            fontWeight: FontWeight.bold,
                                            color: Colors.white,
                                            letterSpacing: -0.5)),
                                    const SizedBox(height: 12),
                                    Text("What's on your mind today?",
                                        style: TextStyle(
                                            fontSize: 18,
                                            color: Colors.white.withValues(alpha: 0.6))),
                                    const SizedBox(height: 48),
                                  ],
                                ),
                              ),
                            ),
                          ),'''
)

lines = content.split('\n')
out_lines = []
skip = False

for i, line in enumerate(lines):
    # Specifically match the line that has Container( and is around line 1222
    if 'Container(' in line and 'constraints: const BoxConstraints(maxWidth: 800),' in lines[i+1] and i > 1200 and i < 1250:
        skip = True
        out_lines.append(line[:line.index('Container(')] + 'ChatInputPill(controller: _controller, onSend: () => _handleSend(_controller.text)),')
    if skip:
        if '                        ), // End Container' in line:
            skip = False
    else:
        out_lines.append(line)

content = '\n'.join(out_lines)

# Fix missing Positioned.fill closing bracket
content = content.replace(
'''                  ), // End AnimatedAlign
                ), // End SafeArea
              ); // End return Container''',
'''                  ), // End AnimatedAlign
                ), // End SafeArea
              )); // End return Positioned.fill'''
)

# Move Consumer outside Column
content = content.replace(
'''            }), // End Consumer
          ], // End main Column children
        ), // End main Column''',
'''          ], // End main Column children
        ), // End main Column
            Consumer(builder: (context, ref, child) {
              final isListening = ref.watch(chatProvider).isListening;
              final isSending = ref.watch(chatProvider).isSending;
              final isProcessing = ref.watch(chatProvider).isProcessing;
              final isEmpty = ref.watch(chatProvider).messages.isEmpty;
              final isContinuousVoiceMode = ref.watch(chatProvider).isContinuousVoiceMode;
              return SizedBox.shrink(); // Replaced below
            }), // This will be removed'''
)

with open(r'apps\client\web\lib\chat_view.dart', 'w', encoding='utf-8') as f:
    f.write(content)
