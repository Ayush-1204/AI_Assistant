import sys

with open('apps/client/web/lib/api_client.dart', 'r') as f:
    content = f.read()

# Remove import
content = content.replace("import 'models/conversation_info.dart';\n", "")

# Remove fetchConversations
to_remove = '''  Future<List<ConversationInfo>> fetchConversations() async {
    try {
      final response = await _dio.get('/conversations');
      if (response.data is List) {
        return (response.data as List).map((c) => ConversationInfo.fromJson(c)).toList();
      }
      return [];
    } catch (e) {
      print('fetchConversations error: ');
      return [];
    }
  }

'''
content = content.replace(to_remove, "")

with open('apps/client/web/lib/api_client.dart', 'w') as f:
    f.write(content)
