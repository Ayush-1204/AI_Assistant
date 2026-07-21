import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'providers/tasks_provider.dart';

class TasksView extends ConsumerStatefulWidget {
  const TasksView({super.key});

  @override
  ConsumerState<TasksView> createState() => _TasksViewState();
}

class _TasksViewState extends ConsumerState<TasksView> {
  TaskItem? _selectedTask;
  final List<String> _columns = ['To Do', 'In Progress', 'Under Review', 'Done'];

  final Map<String, Color> _priorityColors = {
    'High': Colors.redAccent,
    'Medium': Colors.orangeAccent,
    'Low': Colors.grey,
  };

  final Map<String, Color> _statusColors = {
    'To Do': Colors.grey,
    'In Progress': Colors.blueAccent,
    'Under Review': Colors.purpleAccent,
    'Done': Colors.green,
  };

  @override
  Widget build(BuildContext context) {
    final tState = ref.watch(tasksProvider);

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildHeader(),
                Expanded(
                  child: tState.isLoading && tState.tasks.isEmpty
                      ? const Center(child: CircularProgressIndicator(color: Colors.white24))
                      : _buildKanbanBoard(tState.tasks),
                ),
              ],
            ),
          ),
          if (_selectedTask != null) _buildInspector(),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Sprint Alpha',
                  style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                      letterSpacing: -0.01)),
              const SizedBox(height: 4),
              Text('Manage project deliverables natively synced with Google Tasks.',
                  style: TextStyle(fontSize: 16, color: Colors.white.withValues(alpha: 0.6))),
            ],
          ),
          ElevatedButton.icon(
            onPressed: _showNewTaskDialog,
            icon: const Icon(Icons.add, size: 18),
            label: const Text('New Task'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white.withValues(alpha: 0.1),
              foregroundColor: Colors.white,
              elevation: 0,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
                side: BorderSide(color: Colors.white.withValues(alpha: 0.3)),
              ),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildKanbanBoard(List<TaskItem> tasks) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: _columns.map((col) {
          final colTasks = tasks.where((t) => t.status == col).toList();
          return _buildColumn(col, colTasks);
        }).toList(),
      ),
    );
  }

  Widget _buildColumn(String title, List<TaskItem> tasks) {
    return DragTarget<TaskItem>(
      onAcceptWithDetails: (details) {
        final task = details.data;
        if (task.status != title) {
          ref.read(tasksProvider.notifier).updateTaskStatus(task.id, title);
        }
      },
      builder: (context, candidateData, rejectedData) {
        final isHovering = candidateData.isNotEmpty;
        final cColor = _statusColors[title] ?? Colors.white;

        return Container(
          width: 320,
          margin: const EdgeInsets.only(right: 24),
          decoration: BoxDecoration(
            color: isHovering ? Colors.white.withValues(alpha: 0.05) : Colors.white.withValues(alpha: 0.02),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: isHovering ? cColor.withValues(alpha: 0.5) : Colors.white.withValues(alpha: 0.05)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Container(width: 8, height: 8, decoration: BoxDecoration(shape: BoxShape.circle, color: cColor)),
                        const SizedBox(width: 8),
                        Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white)),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12)),
                          child: Text('${tasks.length}', style: TextStyle(fontSize: 12, color: Colors.white.withValues(alpha: 0.5))),
                        )
                      ],
                    ),
                    Icon(Icons.add, size: 16, color: Colors.white.withValues(alpha: 0.5)),
                  ],
                ),
              ),
              const Divider(height: 1, color: Colors.white10),
              Flexible(
                child: ListView.separated(
                  shrinkWrap: true,
                  physics: const ClampingScrollPhysics(),
                  padding: const EdgeInsets.all(12),
                  itemCount: tasks.length,
                  separatorBuilder: (ctx, i) => const SizedBox(height: 12),
                  itemBuilder: (ctx, i) {
                    final t = tasks[i];
                    return Draggable<TaskItem>(
                      data: t,
                      feedback: Material(
                        color: Colors.transparent,
                        child: Opacity(opacity: 0.8, child: SizedBox(width: 300, child: _buildTaskCard(t))),
                      ),
                      childWhenDragging: Opacity(opacity: 0.3, child: _buildTaskCard(t)),
                      child: _buildTaskCard(t),
                    );
                  },
                ),
              )
            ],
          ),
        );
      },
    );
  }

  Widget _buildTaskCard(TaskItem task) {
    final pColor = _priorityColors[task.priority] ?? Colors.grey;
    final isDone = task.status == 'Done';

    return InkWell(
      onTap: () => setState(() => _selectedTask = task),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.04),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: _selectedTask?.id == task.id ? Colors.white30 : Colors.white10),
          boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.2), blurRadius: 4, offset: const Offset(0, 2))],
        ),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: pColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: pColor.withValues(alpha: 0.3)),
                  ),
                  child: Text(task.priority.toUpperCase(),
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5, color: pColor)),
                ),
                InkWell(
                  onTap: () => _confirmDelete(task),
                  child: Icon(Icons.more_horiz, size: 16, color: Colors.white.withValues(alpha: 0.5)),
                )
              ],
            ),
            const SizedBox(height: 8),
            Text(task.title,
                style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    color: isDone ? Colors.white54 : Colors.white,
                    decoration: isDone ? TextDecoration.lineThrough : null)),
            if (task.notes.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                task.notes,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 14, color: Colors.white.withValues(alpha: 0.5)),
              ),
            ],
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                if (task.due != null)
                  Row(
                    children: [
                      Icon(Icons.calendar_today, size: 12, color: Colors.white.withValues(alpha: 0.5)),
                      const SizedBox(width: 4),
                      Text(task.due!.split('T')[0],
                          style: TextStyle(fontSize: 12, color: Colors.white.withValues(alpha: 0.5))),
                    ],
                  )
                else
                  const SizedBox(),
                if (isDone)
                   Row(
                    children: [
                      const Icon(Icons.check_circle, size: 12, color: Colors.green),
                      const SizedBox(width: 4),
                      Text('Completed',
                          style: TextStyle(fontSize: 12, color: Colors.green.withValues(alpha: 0.8))),
                    ],
                  )
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildInspector() {
    final task = _selectedTask!;
    return Container(
      width: 320,
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.02),
        border: Border(left: BorderSide(color: Colors.white.withValues(alpha: 0.05))),
      ),
      child: ClipRRect(
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('Task Details', style: TextStyle(fontSize: 24, color: Colors.white, fontWeight: FontWeight.w600)),
                    IconButton(
                      icon: const Icon(Icons.close, color: Colors.white54),
                      onPressed: () => setState(() => _selectedTask = null),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Container(width: 8, height: 8, decoration: BoxDecoration(shape: BoxShape.circle, color: _statusColors[task.status] ?? Colors.white)),
                    const SizedBox(width: 8),
                    Text(task.status, style: TextStyle(fontSize: 14, color: Colors.white.withValues(alpha: 0.6))),
                  ],
                ),
                const SizedBox(height: 24),
                Text(task.title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600, color: Colors.white)),
                const SizedBox(height: 12),
                if (task.notes.isNotEmpty)
                  Text(task.notes, style: TextStyle(fontSize: 14, height: 1.5, color: Colors.white.withValues(alpha: 0.7))),
                
                const SizedBox(height: 24),
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.02),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
                  ),
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      _buildInspectorRow('Assignee', 'Me'),
                      const SizedBox(height: 12),
                      _buildInspectorRow('Due Date', task.due?.split('T')[0] ?? 'None'),
                      const SizedBox(height: 12),
                      _buildInspectorRow('Priority', task.priority),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildInspectorRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: TextStyle(fontSize: 14, color: Colors.white.withValues(alpha: 0.5))),
        Text(value, style: const TextStyle(fontSize: 14, color: Colors.white, fontWeight: FontWeight.w500)),
      ],
    );
  }

  void _showNewTaskDialog() {
    // Basic dialog for creating a new task, simplified for space
    String title = '';
    String priority = 'Medium';
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E1E1E),
        title: const Text('New Kanban Task', style: TextStyle(color: Colors.white)),
        content: TextField(
          autofocus: true,
          style: const TextStyle(color: Colors.white),
          decoration: const InputDecoration(hintText: 'Task Title', hintStyle: TextStyle(color: Colors.white54)),
          onChanged: (v) => title = v,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              if (title.isNotEmpty) {
                ref.read(tasksProvider.notifier).createTask(title, priority, 'To Do');
              }
              Navigator.pop(ctx);
            },
            child: const Text('Create'),
          )
        ],
      ),
    );
  }

  void _confirmDelete(TaskItem task) {
    ref.read(tasksProvider.notifier).deleteTask(task.id);
    if (_selectedTask?.id == task.id) {
      setState(() => _selectedTask = null);
    }
  }
}
