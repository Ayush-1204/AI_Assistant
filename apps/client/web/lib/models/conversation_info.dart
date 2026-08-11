class ConversationInfo {
  final int id;
  final int userId;
  final String title;
  final bool isPinned;
  final DateTime createdAt;
  final DateTime updatedAt;

  ConversationInfo({
    required this.id,
    required this.userId,
    required this.title,
    required this.isPinned,
    required this.createdAt,
    required this.updatedAt,
  });

  factory ConversationInfo.fromJson(Map<String, dynamic> json) {
    return ConversationInfo(
      id: json['id'],
      userId: json['user_id'],
      title: json['title'] ?? 'New Chat',
      isPinned: json['is_pinned'] ?? false,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
}
