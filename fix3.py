import os

with open(r'apps\client\web\lib\api_client.dart', 'r', encoding='utf-8') as f:
    content = f.read()

old_fetch = '''  Future<List<dynamic>> fetchConversations() async {
    try {
      final response = await _dio.get('/conversations');
      return response.data as List<dynamic>;
    } catch (_) {
      return [];
    }
  }'''

content = content.replace(old_fetch, '')

with open(r'apps\client\web\lib\api_client.dart', 'w', encoding='utf-8') as f:
    f.write(content)

with open(r'apps\client\web\lib\chat_view.dart', 'r', encoding='utf-8') as f:
    content2 = f.read()

if "import 'widgets/chat_input_pill.dart';" not in content2:
    content2 = content2.replace("import 'package:flutter/material.dart';", "import 'package:flutter/material.dart';\nimport 'widgets/chat_input_pill.dart';")

with open(r'apps\client\web\lib\chat_view.dart', 'w', encoding='utf-8') as f:
    f.write(content2)

