import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Global provider to control the main layout's active section index.
final navIndexProvider = StateProvider<int>((ref) => 0);
