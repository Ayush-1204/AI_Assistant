import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'auth_provider.dart';

final libraryProvider = FutureProvider.family.autoDispose<List<dynamic>, bool>((ref, isDeleted) async {
  final apiClient = ref.read(apiClientProvider);
  final docs = await apiClient.fetchDocuments(isDeleted: isDeleted);
  // Sort documents by created_at descending
  docs.sort((a, b) {
    final dateA = DateTime.tryParse(a['created_at'] ?? '') ?? DateTime.fromMillisecondsSinceEpoch(0);
    final dateB = DateTime.tryParse(b['created_at'] ?? '') ?? DateTime.fromMillisecondsSinceEpoch(0);
    return dateB.compareTo(dateA);
  });
  return docs;
});
