import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api_client.dart';
import 'auth_provider.dart';

class TaskItem {
  final String id;
  final String title;
  final String? due;
  final String status;
  final String priority;
  final String notes;

  TaskItem({
    required this.id,
    required this.title,
    this.due,
    required this.status,
    required this.priority,
    required this.notes,
  });

  factory TaskItem.fromJson(Map<String, dynamic> json) {
    return TaskItem(
      id: json['id']?.toString() ?? '',
      title: json['title'] ?? '',
      due: json['due'],
      status: json['status'] ?? 'To Do',
      priority: json['priority'] ?? 'Medium',
      notes: json['notes'] ?? '',
    );
  }

  TaskItem copyWith({
    String? id,
    String? title,
    String? due,
    String? status,
    String? priority,
    String? notes,
  }) {
    return TaskItem(
      id: id ?? this.id,
      title: title ?? this.title,
      due: due ?? this.due,
      status: status ?? this.status,
      priority: priority ?? this.priority,
      notes: notes ?? this.notes,
    );
  }
}

class TasksState {
  final bool isLoading;
  final List<TaskItem> tasks;
  final String? error;

  TasksState({
    this.isLoading = false,
    this.tasks = const [],
    this.error,
  });

  TasksState copyWith({
    bool? isLoading,
    List<TaskItem>? tasks,
    String? error,
  }) {
    return TasksState(
      isLoading: isLoading ?? this.isLoading,
      tasks: tasks ?? this.tasks,
      error: error,
    );
  }
}

class TasksNotifier extends StateNotifier<TasksState> {
  final ApiClient _apiClient;

  TasksNotifier(this._apiClient) : super(TasksState()) {
    fetchTasks();
  }

  Future<void> fetchTasks() async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final res = await _apiClient.fetchTasks();
      final list = res.map((e) => TaskItem.fromJson(e)).toList();
      state = state.copyWith(isLoading: false, tasks: list);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> createTask(String title, String priority, String status, {String? due, String? notes}) async {
    try {
      final res = await _apiClient.createTask({
        'title': title,
        'priority': priority,
        'status': status,
        if (due != null) 'due_date': due,
        if (notes != null) 'notes': notes,
      });
      final nt = TaskItem.fromJson(res);
      state = state.copyWith(tasks: [...state.tasks, nt]);
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  Future<void> updateTaskStatus(String id, String newStatus) async {
    // Optimistic update
    final tIdx = state.tasks.indexWhere((t) => t.id == id);
    if (tIdx == -1) return;
    final oldTask = state.tasks[tIdx];
    final nt = oldTask.copyWith(status: newStatus);
    
    final updatedList = List<TaskItem>.from(state.tasks);
    updatedList[tIdx] = nt;
    state = state.copyWith(tasks: updatedList);

    try {
      await _apiClient.updateTaskStatus(id, newStatus);
    } catch (e) {
      // Revert on error
      updatedList[tIdx] = oldTask;
      state = state.copyWith(tasks: updatedList, error: e.toString());
    }
  }

  Future<void> deleteTask(String id) async {
    final oldList = state.tasks;
    state = state.copyWith(tasks: state.tasks.where((t) => t.id != id).toList());
    try {
      await _apiClient.deleteTask(id);
    } catch (e) {
      state = state.copyWith(tasks: oldList, error: e.toString());
    }
  }
}

final tasksProvider = StateNotifierProvider<TasksNotifier, TasksState>((ref) {
  final api = ref.watch(apiClientProvider);
  return TasksNotifier(api);
});
