import os

with open(r'apps\client\web\lib\chat_view.dart', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Rename _HoverableAttachmentPill
for i in range(len(lines)):
    lines[i] = lines[i].replace('_HoverableAttachmentPill', 'HoverableAttachmentPill')

# Find the start of the Container
start_idx = -1
for i in range(len(lines)):
    if 'Container(' in lines[i] and 'constraints: const BoxConstraints(maxWidth: 800),' in lines[i+1] and i > 1200 and i < 1250:
        start_idx = i
        break

if start_idx != -1:
    end_idx = -1
    for i in range(start_idx, len(lines)):
        if '                        ), // End Container' in lines[i]:
            end_idx = i
            break
    
    if end_idx != -1:
        # We replace the lines from start_idx to end_idx (inclusive)
        replacement = '                        ChatInputPill(controller: _controller, onSend: () => _handleSend(_controller.text)),\n'
        lines = lines[:start_idx] + [replacement] + lines[end_idx+1:]

content = "".join(lines)

# Now we need to modify the animated center layout.
content = content.replace(
    'padding: const EdgeInsets.fromLTRB(0, 24, 0, 24),',
    'padding: const EdgeInsets.fromLTRB(0, 24, 0, 200),'
)

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

# Fix Positioned.fill ending bracket
content = content.replace(
'''                  ), // End AnimatedAlign
                ), // End SafeArea
              ); // End return Container''',
'''                  ), // End AnimatedAlign
                ), // End SafeArea
              )); // End return Positioned.fill'''
)

# And add the imports
content = content.replace("import 'workspace_view.dart';", "import 'workspace_view.dart';\nimport 'widgets/chat_input_pill.dart';")

with open(r'apps\client\web\lib\chat_view.dart', 'w', encoding='utf-8') as f:
    f.write(content)

print(start_idx, end_idx)
