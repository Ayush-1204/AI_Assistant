import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'auth_provider.dart';

final notesProvider = FutureProvider<List<dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  return api.fetchNotes();
});

final documentsProvider = FutureProvider<List<dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  return api.fetchDocuments();
});
