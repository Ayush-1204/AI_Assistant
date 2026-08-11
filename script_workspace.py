import os
with open(r'apps\client\web\lib\workspace_view.dart', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# add import
content = "".join(lines)
content = content.replace("import 'providers/auth_provider.dart';", "import 'providers/auth_provider.dart';\nimport 'widgets/chat_input_pill.dart';")
lines = content.split('\n')

start_idx = -1
for i in range(len(lines)):
    if 'Container(' in lines[i] and 'constraints: const BoxConstraints(maxWidth: 800),' in lines[i+1]:
        start_idx = i
        break

if start_idx != -1:
    end_idx = -1
    for i in range(start_idx, len(lines)):
        if '                        ), // End Action buttons container' in lines[i]:
            # Wait, the structure here might be slightly different than chat_view.dart
            # Let's just find the closing bracket of the Container
            pass
