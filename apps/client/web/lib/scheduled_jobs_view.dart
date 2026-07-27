import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'providers/auth_provider.dart';

// ─────────────────────────────────────────────────────────────────────────────
// PROVIDER
// ─────────────────────────────────────────────────────────────────────────────
final scheduledJobsProvider =
    StateNotifierProvider<ScheduledJobsNotifier, AsyncValue<List<Map<String, dynamic>>>>(
  (ref) {
    final api = ref.watch(apiClientProvider);
    return ScheduledJobsNotifier(api);
  },
);

class ScheduledJobsNotifier
    extends StateNotifier<AsyncValue<List<Map<String, dynamic>>>> {
  final dynamic _api;
  ScheduledJobsNotifier(this._api) : super(const AsyncValue.loading()) {
    refresh();
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    try {
      final data = await _api.fetchScheduledTasks();
      state = AsyncValue.data(List<Map<String, dynamic>>.from(
        (data as List).map((e) => Map<String, dynamic>.from(e as Map)),
      ));
    } catch (e, s) {
      state = AsyncValue.error(e, s);
    }
  }

  Future<void> toggle(int id) async {
    try {
      await _api.toggleScheduledTask(id);
      refresh();
    } catch (e) {
      debugPrint('toggle error: $e');
    }
  }

  Future<void> delete(int id) async {
    try {
      await _api.deleteScheduledTask(id);
      refresh();
    } catch (e) {
      debugPrint('delete error: $e');
    }
  }

  Future<void> create({
    required String label,
    required String directive,
    String? cronExpression,
    DateTime? runAt,
  }) async {
    try {
      await _api.createScheduledTask(
        label: label,
        directive: directive,
        cronExpression: cronExpression,
        runAt: runAt,
      );
      refresh();
    } catch (e) {
      debugPrint('create error: $e');
      rethrow;
    }
  }

  Future<void> update({
    required int id,
    String? label,
    String? directive,
    String? cronExpression,
    DateTime? runAt,
    DateTime? endRepeatAt,
  }) async {
    try {
      await _api.updateScheduledTask(
        id: id,
        label: label,
        directive: directive,
        cronExpression: cronExpression,
        runAt: runAt,
        endRepeatAt: endRepeatAt,
      );
      refresh();
    } catch (e) {
      debugPrint('update error: $e');
      rethrow;
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN VIEW
// ─────────────────────────────────────────────────────────────────────────────
class ScheduledJobsView extends ConsumerWidget {
  const ScheduledJobsView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final jobsAsync = ref.watch(scheduledJobsProvider);

    return Column(
      children: [
        // Header
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface.withValues(alpha: 0.8),
            border: Border(
              bottom: BorderSide(color: Colors.white.withValues(alpha: 0.05)),
            ),
          ),
          child: Row(
            children: [
              const Icon(Icons.schedule_outlined,
                  color: Colors.white70, size: 20),
              const SizedBox(width: 12),
              const Text(
                'Scheduled Agent Jobs',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w600,
                  letterSpacing: -0.5,
                  color: Colors.white,
                ),
              ),
              const Spacer(),
              _RefreshButton(onTap: () => ref.read(scheduledJobsProvider.notifier).refresh()),
              const SizedBox(width: 8),
              _NewJobButton(),
            ],
          ),
        ),

        // Body
        Expanded(
          child: jobsAsync.when(
            loading: () => const Center(
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            error: (e, _) => Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.error_outline,
                      color: Colors.redAccent.withValues(alpha: 0.7), size: 40),
                  const SizedBox(height: 12),
                  Text('Failed to load jobs: $e',
                      style: TextStyle(color: Colors.white.withValues(alpha: 0.5))),
                ],
              ),
            ),
            data: (jobs) => jobs.isEmpty
                ? _EmptyState()
                : ListView.builder(
                    padding: const EdgeInsets.all(24),
                    itemCount: jobs.length,
                    itemBuilder: (ctx, i) => _JobCard(job: jobs[i]),
                  ),
          ),
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// JOB CARD
// ─────────────────────────────────────────────────────────────────────────────
class _JobCard extends ConsumerStatefulWidget {
  final Map<String, dynamic> job;
  const _JobCard({required this.job});

  @override
  ConsumerState<_JobCard> createState() => _JobCardState();
}

class _JobCardState extends ConsumerState<_JobCard> {
  bool _isHovered = false;

  Color _statusColor(String status) {
    switch (status.toUpperCase()) {
      case 'PENDING':
        return const Color(0xFF7B8CDE);
      case 'RUNNING':
        return const Color(0xFFFFB300);
      case 'COMPLETED':
        return const Color(0xFF4CAF50);
      case 'FAILED':
        return Colors.redAccent;
      default:
        return Colors.white38;
    }
  }

  String _formatDateTime(String? iso) {
    if (iso == null) return 'N/A';
    try {
      final dt = DateTime.parse(iso).toLocal();
      final months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      final hour = dt.hour.toString().padLeft(2, '0');
      final min = dt.minute.toString().padLeft(2, '0');
      return '${months[dt.month - 1]} ${dt.day}, ${dt.year}  $hour:$min';
    } catch (_) {
      return iso;
    }
  }

  @override
  Widget build(BuildContext context) {
    final job = widget.job;
    final isEnabled = job['is_enabled'] as bool? ?? true;
    final status = job['status'] as String? ?? 'PENDING';
    final isCron = job['cron_expression'] != null;
    final color = _statusColor(status);

    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.0, end: 1.0),
      duration: const Duration(milliseconds: 350),
      curve: Curves.easeOutCubic,
      builder: (ctx, val, child) => Transform.translate(
        offset: Offset(0, 12 * (1 - val)),
        child: Opacity(opacity: val, child: child),
      ),
      child: MouseRegion(
        onEnter: (_) => setState(() => _isHovered = true),
        onExit: (_) => setState(() => _isHovered = false),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 250),
          margin: const EdgeInsets.only(bottom: 16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [
                const Color(0xFF1E1E1E).withValues(alpha: isEnabled ? 0.9 : 0.5),
                const Color(0xFF151515).withValues(alpha: isEnabled ? 0.9 : 0.5),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: _isHovered && isEnabled
                  ? color.withValues(alpha: 0.3)
                  : Colors.white.withValues(alpha: 0.05),
              width: 1.5,
            ),
            boxShadow: _isHovered && isEnabled
                ? [
                    BoxShadow(
                      color: color.withValues(alpha: 0.08),
                      blurRadius: 20,
                      spreadRadius: -5,
                    )
                  ]
                : [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.2),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    )
                  ],
          ),
          child: AnimatedOpacity(
            duration: const Duration(milliseconds: 250),
            opacity: isEnabled ? 1.0 : 0.4,
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Top row (Title, Status, Actions)
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      // Glowing dot
                      Container(
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: color,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: color.withValues(alpha: 0.6),
                              blurRadius: 8,
                              spreadRadius: 2,
                            )
                          ],
                        ),
                      ),
                      const SizedBox(width: 16),
                      // Title
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              job['label'] as String? ?? 'Unnamed Job',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 0.3,
                              ),
                            ),
                            const SizedBox(height: 4),
                            // Metadata (Cron/One-shot)
                            Row(
                              children: [
                                if (isCron) ...[
                                  Icon(Icons.repeat, size: 12, color: Colors.white.withValues(alpha: 0.4)),
                                  const SizedBox(width: 4),
                                  Text(
                                    job['cron_expression'] as String,
                                    style: TextStyle(
                                      color: Colors.white.withValues(alpha: 0.4),
                                      fontSize: 12,
                                      fontFamily: 'monospace',
                                    ),
                                  ),
                                ] else ...[
                                  Icon(Icons.calendar_today, size: 12, color: Colors.white.withValues(alpha: 0.4)),
                                  const SizedBox(width: 4),
                                  Text(
                                    'One-shot',
                                    style: TextStyle(
                                      color: Colors.white.withValues(alpha: 0.4),
                                      fontSize: 12,
                                    ),
                                  ),
                                ],
                                const SizedBox(width: 12),
                                // Status Pill
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: color.withValues(alpha: 0.15),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(color: color.withValues(alpha: 0.3)),
                                  ),
                                  child: Text(
                                    status,
                                    style: TextStyle(
                                      color: color,
                                      fontSize: 10,
                                      fontWeight: FontWeight.w700,
                                      letterSpacing: 0.5,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      
                      // Actions
                      AnimatedOpacity(
                        duration: const Duration(milliseconds: 200),
                        opacity: _isHovered ? 1.0 : 0.6,
                        child: Row(
                          children: [
                            // Edit
                            IconButton(
                              icon: const Icon(Icons.edit_outlined, size: 20, color: Colors.white54),
                              tooltip: 'Edit job',
                              splashRadius: 20,
                              onPressed: () {
                                showDialog(
                                  context: context,
                                  builder: (ctx) => _TaskDialog(
                                    job: job,
                                    onSave: ({
                                      required String label,
                                      required String directive,
                                      String? cronExpression,
                                      DateTime? runAt,
                                      DateTime? endRepeatAt,
                                    }) async {
                                      await ref.read(scheduledJobsProvider.notifier).update(
                                            id: job['id'] as int,
                                            label: label,
                                            directive: directive,
                                            cronExpression: cronExpression,
                                            runAt: runAt,
                                            endRepeatAt: endRepeatAt,
                                          );
                                    },
                                  ),
                                );
                              },
                            ),
                            // Delete
                            IconButton(
                              icon: const Icon(Icons.delete_outline, size: 20, color: Colors.white54),
                              tooltip: 'Delete job',
                              splashRadius: 20,
                              onPressed: () async {
                                final confirm = await showDialog<bool>(
                                  context: context,
                                  builder: (ctx) => AlertDialog(
                                    backgroundColor: const Color(0xFF1B1B1B),
                                    title: const Text('Delete Job', style: TextStyle(color: Colors.white)),
                                    content: Text(
                                      'Delete "${job['label']}"? This cannot be undone.',
                                      style: TextStyle(color: Colors.white.withValues(alpha: 0.6)),
                                    ),
                                    actions: [
                                      TextButton(
                                        onPressed: () => Navigator.pop(ctx, false),
                                        child: const Text('Cancel', style: TextStyle(color: Colors.white54)),
                                      ),
                                      ElevatedButton(
                                        onPressed: () => Navigator.pop(ctx, true),
                                        style: ElevatedButton.styleFrom(
                                          backgroundColor: Colors.redAccent.withValues(alpha: 0.2),
                                        ),
                                        child: const Text('Delete', style: TextStyle(color: Colors.redAccent)),
                                      ),
                                    ],
                                  ),
                                );
                                if (confirm == true) {
                                  ref.read(scheduledJobsProvider.notifier).delete(job['id'] as int);
                                }
                              },
                            ),
                            const SizedBox(width: 8),
                            // Toggle switch
                            Switch.adaptive(
                              value: isEnabled,
                              onChanged: (_) =>
                                  ref.read(scheduledJobsProvider.notifier).toggle(job['id'] as int),
                              activeColor: const Color(0xFF7B8CDE),
                              inactiveThumbColor: Colors.white30,
                              inactiveTrackColor: Colors.white10,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // Directive
                  if (job['directive'] != null)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.02),
                        borderRadius: BorderRadius.circular(8),
                        border: Border(
                          left: BorderSide(color: color.withValues(alpha: 0.5), width: 4),
                        ),
                      ),
                      child: Text(
                        job['directive'] as String,
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.7),
                          fontSize: 13,
                          height: 1.5,
                          fontStyle: FontStyle.italic,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),

                  const SizedBox(height: 16),
                  
                  // Footer: Next Run
                  Row(
                    children: [
                      Icon(Icons.access_time, size: 14, color: Colors.white.withValues(alpha: 0.3)),
                      const SizedBox(width: 6),
                      Text(
                        'Next: ${_formatDateTime(job['next_run_at'] as String?)}',
                        style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.4),
                          fontSize: 12,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}


class _EmptyState extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.event_busy, size: 64, color: Colors.white.withValues(alpha: 0.1)),
          const SizedBox(height: 16),
          Text(
            'No scheduled jobs yet',
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.5),
              fontSize: 16,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}

class _NewJobButton extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ElevatedButton.icon(
      onPressed: () {
        showDialog(
          context: context,
          builder: (ctx) => _TaskDialog(
            onSave: ({
              required String label,
              required String directive,
              String? cronExpression,
              DateTime? runAt,
              DateTime? endRepeatAt,
            }) async {
              await ref.read(scheduledJobsProvider.notifier).create(
                    label: label,
                    directive: directive,
                    cronExpression: cronExpression,
                    runAt: runAt,
                  );
            },
          ),
        );
      },
      icon: const Icon(Icons.add, size: 16),
      label: const Text('New Job'),
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF7B8CDE).withValues(alpha: 0.15),
        foregroundColor: const Color(0xFF7B8CDE),
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
    );
  }
}

class _TaskDialog extends StatefulWidget {
  final Map<String, dynamic>? job;
  final Future<void> Function({
    required String label,
    required String directive,
    String? cronExpression,
    DateTime? runAt,
    DateTime? endRepeatAt,
  }) onSave;

  const _TaskDialog({required this.onSave, this.job});

  @override
  State<_TaskDialog> createState() => _TaskDialogState();
}

class _TaskDialogState extends State<_TaskDialog> {
  late TextEditingController _labelCtrl;
  late TextEditingController _directiveCtrl;
  bool _isCron = true;
  bool _isLoading = false;
  DateTime? _runAt;
  
  String _repeat = 'Daily';
  String _time = 'Morning';
  TimeOfDay? _customTime;
  
  String _endRepeat = 'Never';
  DateTime? _endRepeatAt;
  
  String? _error;

  @override
  void initState() {
    super.initState();
    final job = widget.job;
    _labelCtrl = TextEditingController(text: job?['label'] ?? '');
    _directiveCtrl = TextEditingController(text: job?['directive'] ?? '');
    
    if (job != null) {
      if (job['cron_expression'] != null) {
        _isCron = true;
        _parseCron(job['cron_expression'] as String);
      } else if (job['scheduled_time'] != null) {
        _isCron = false;
        _runAt = DateTime.tryParse(job['scheduled_time'] as String)?.toLocal();
      }
      if (job['end_repeat_at'] != null) {
        _endRepeat = 'On Date';
        _endRepeatAt = DateTime.tryParse(job['end_repeat_at'] as String)?.toLocal();
      }
    }
  }
  
  void _parseCron(String cron) {
    final parts = cron.split(' ');
    if (parts.length >= 5) {
      final hour = parts[1];
      final dayOfWeek = parts[4];
      final dom = parts[2];
      
      if (hour != '*') {
        int h = int.tryParse(hour) ?? 8;
        if (h == 8) _time = 'Morning';
        else if (h == 14) _time = 'Afternoon';
        else if (h == 20) _time = 'Evening';
        else if (h == 0) _time = 'Midnight';
        else {
          _time = 'Custom';
          _customTime = TimeOfDay(hour: h, minute: 0);
        }
      }
      
      if (dayOfWeek == '1-5') _repeat = 'Weekdays';
      else if (dayOfWeek == '1') _repeat = 'Weekly';
      else if (dom == '1' && parts[3] == '*') _repeat = 'Monthly';
      else if (dom == '1' && parts[3] == '1') _repeat = 'Yearly';
      else _repeat = 'Daily';
    }
  }

  @override
  void dispose() {
    _labelCtrl.dispose();
    _directiveCtrl.dispose();
    super.dispose();
  }

  String _generateCron() {
    int hour = 8;
    int minute = 0;
    switch (_time) {
      case 'Morning': hour = 8; break;
      case 'Afternoon': hour = 14; break;
      case 'Evening': hour = 20; break;
      case 'Midnight': hour = 0; break;
      case 'Custom': 
        if (_customTime != null) {
          hour = _customTime!.hour;
          minute = _customTime!.minute;
        }
        break;
    }
    
    switch (_repeat) {
      case 'Daily': return '$minute $hour * * *';
      case 'Weekdays': return '$minute $hour * * 1-5';
      case 'Weekly': return '$minute $hour * * 1';
      case 'Monthly': return '$minute $hour 1 * *';
      case 'Yearly': return '$minute $hour 1 1 *';
      default: return '$minute $hour * * *';
    }
  }

  Future<void> _submit() async {
    final label = _labelCtrl.text.trim();
    final directive = _directiveCtrl.text.trim();

    if (label.isEmpty || directive.isEmpty) {
      setState(() => _error = 'Label and directive are required.');
      return;
    }

    if (!_isCron && _runAt == null) {
      setState(() => _error = 'Pick a date/time for the one-shot run.');
      return;
    }
    
    if (_isCron && _endRepeat == 'On Date' && _endRepeatAt == null) {
      setState(() => _error = 'Pick an end date.');
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      await widget.onSave(
        label: label,
        directive: directive,
        cronExpression: _isCron ? _generateCron() : null,
        runAt: _isCron ? null : _runAt,
        endRepeatAt: (_isCron && _endRepeat == 'On Date') ? _endRepeatAt : null,
      );
      if (mounted) Navigator.pop(context);
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = e.toString().replaceFirst('Exception: ', '');
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: const Color(0xFF1A1A1A),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 520),
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: const Color(0xFF7B8CDE).withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(widget.job == null ? Icons.add_alarm : Icons.edit_calendar,
                        color: const Color(0xFF7B8CDE), size: 20),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    widget.job == null ? 'New Scheduled Job' : 'Edit Scheduled Job',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              _FieldLabel('Job Name'),
              const SizedBox(height: 6),
              _buildTextField(_labelCtrl, 'e.g. Weekly Summary Email'),
              const SizedBox(height: 16),

              _FieldLabel('Agent Directive'),
              const SizedBox(height: 6),
              _buildTextField(
                _directiveCtrl,
                'What should the agent do? e.g. Summarize my week and email it to me.',
                maxLines: 3,
              ),
              const SizedBox(height: 16),

              Row(
                children: [
                  _TypeChip(
                    label: 'Recurring',
                    icon: Icons.repeat,
                    selected: _isCron,
                    onTap: () => setState(() => _isCron = true),
                  ),
                  const SizedBox(width: 12),
                  _TypeChip(
                    label: 'One-Shot',
                    icon: Icons.play_arrow,
                    selected: !_isCron,
                    onTap: () => setState(() => _isCron = false),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              if (_isCron) ...[
                const SizedBox(height: 8),
                _buildDropdown('Repeat', _repeat, ['Daily', 'Weekdays', 'Weekly', 'Monthly', 'Yearly'], (v) {
                  if (v != null) setState(() => _repeat = v);
                }),
                
                _buildDropdown('Time', _time, ['Morning', 'Afternoon', 'Evening', 'Midnight', 'Custom'], (v) async {
                  if (v != null) {
                    if (v == 'Custom') {
                      final time = await showTimePicker(
                        context: context, 
                        initialTime: _customTime ?? const TimeOfDay(hour: 8, minute: 0),
                        builder: (context, child) {
                          return Theme(
                            data: Theme.of(context).copyWith(
                              colorScheme: const ColorScheme.dark(
                                primary: Color(0xFF7B8CDE),
                                onPrimary: Colors.white,
                                surface: Color(0xFF1A1A1A),
                                onSurface: Colors.white,
                              ),
                            ),
                            child: child!,
                          );
                        }
                      );
                      if (time != null) {
                        setState(() {
                           _time = v;
                           _customTime = time;
                        });
                      }
                    } else {
                      setState(() => _time = v);
                    }
                  }
                }),
                
                _buildDropdown('End repeat', _endRepeat, ['Never', 'On Date'], (v) async {
                  if (v != null) {
                    if (v == 'On Date') {
                      final date = await showDatePicker(
                        context: context,
                        initialDate: _endRepeatAt ?? DateTime.now().add(const Duration(days: 1)),
                        firstDate: DateTime.now(),
                        lastDate: DateTime.now().add(const Duration(days: 3650)),
                        builder: (context, child) {
                          return Theme(
                            data: Theme.of(context).copyWith(
                              colorScheme: const ColorScheme.dark(
                                primary: Color(0xFF7B8CDE),
                                onPrimary: Colors.white,
                                surface: Color(0xFF1A1A1A),
                                onSurface: Colors.white,
                              ),
                            ),
                            child: child!,
                          );
                        }
                      );
                      if (date != null) {
                        setState(() {
                          _endRepeat = v;
                          _endRepeatAt = date;
                        });
                      }
                    } else {
                      setState(() {
                         _endRepeat = v;
                         _endRepeatAt = null;
                      });
                    }
                  }
                }),
              ] else ...[
                _FieldLabel('Run At'),
                const SizedBox(height: 6),
                GestureDetector(
                  onTap: () async {
                    final picked = await showDateTimePicker(context);
                    if (picked != null) setState(() => _runAt = picked);
                  },
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.04),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.calendar_today, size: 14, color: Colors.white54),
                        const SizedBox(width: 8),
                        Text(
                          _runAt == null ? 'Pick a date and time...' : _runAt.toString().substring(0, 16),
                          style: TextStyle(
                            color: _runAt == null ? Colors.white30 : Colors.white,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],

              if (_error != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.redAccent.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.redAccent.withValues(alpha: 0.3)),
                  ),
                  child: Text(_error!, style: const TextStyle(color: Colors.redAccent, fontSize: 12)),
                ),
              ],

              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('Cancel', style: TextStyle(color: Colors.white54)),
                  ),
                  const SizedBox(width: 10),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _submit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF7B8CDE),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    ),
                    child: _isLoading
                        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : Text(widget.job == null ? 'Create Job' : 'Save Changes', style: const TextStyle(fontWeight: FontWeight.w600)),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(TextEditingController ctrl, String hint, {int maxLines = 1, String? fontFamily}) {
    return TextField(
      controller: ctrl,
      maxLines: maxLines,
      style: TextStyle(color: Colors.white, fontSize: 13, fontFamily: fontFamily),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.25), fontSize: 13),
        filled: true,
        fillColor: Colors.white.withValues(alpha: 0.04),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: Color(0xFF7B8CDE))),
      ),
    );
  }

  Widget _buildDropdown(String label, String value, List<String> items, ValueChanged<String?> onChanged) {
    String displayValue = value;
    if (label == 'Time' && value == 'Custom' && _customTime != null) {
      displayValue = 'Custom (${_customTime!.format(context)})';
    } else if (label == 'End repeat' && value == 'On Date' && _endRepeatAt != null) {
      displayValue = 'On Date (${_endRepeatAt.toString().substring(0, 10)})';
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.8), fontSize: 13, fontWeight: FontWeight.w500)),
          DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: value,
              dropdownColor: const Color(0xFF222222),
              borderRadius: BorderRadius.circular(16),
              icon: const Icon(Icons.keyboard_arrow_down, size: 16, color: Colors.white54),
              style: const TextStyle(color: Colors.white, fontSize: 13),
              selectedItemBuilder: (BuildContext context) {
                return items.map<Widget>((String item) {
                  return Container(
                    alignment: Alignment.centerRight,
                    child: Text(displayValue, style: const TextStyle(color: Colors.white)),
                  );
                }).toList();
              },
              items: items.map((e) => DropdownMenuItem(
                value: e,
                child: SizedBox(
                  width: 130,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(e),
                      if (e == value) const Icon(Icons.check, size: 16, color: Color(0xFF7B8CDE)),
                    ],
                  ),
                )
              )).toList(),
              onChanged: onChanged,
            ),
          ),
        ],
      ),
    );
  }
}


Widget _FieldLabel(String label) => Text(
      label,
      style: TextStyle(
        color: Colors.white.withValues(alpha: 0.5),
        fontSize: 12,
        fontWeight: FontWeight.w500,
        letterSpacing: 0.3,
      ),
    );

class _TypeChip extends StatelessWidget {
  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  const _TypeChip({
    required this.label,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: selected
              ? const Color(0xFF7B8CDE).withValues(alpha: 0.15)
              : Colors.white.withValues(alpha: 0.04),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: selected
                ? const Color(0xFF7B8CDE).withValues(alpha: 0.5)
                : Colors.white.withValues(alpha: 0.08),
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon,
                size: 13,
                color: selected
                    ? const Color(0xFF7B8CDE)
                    : Colors.white.withValues(alpha: 0.4)),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                color: selected
                    ? const Color(0xFF7B8CDE)
                    : Colors.white.withValues(alpha: 0.4),
                fontSize: 12,
                fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RefreshButton extends StatelessWidget {
  final VoidCallback onTap;
  const _RefreshButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.refresh, color: Colors.white54, size: 18),
      onPressed: onTap,
      tooltip: 'Refresh',
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// DATE-TIME PICKER HELPER
// ─────────────────────────────────────────────────────────────────────────────
Future<DateTime?> showDateTimePicker(BuildContext context) async {
  final date = await showDatePicker(
    context: context,
    initialDate: DateTime.now().add(const Duration(hours: 1)),
    firstDate: DateTime.now(),
    lastDate: DateTime.now().add(const Duration(days: 365)),
    builder: (ctx, child) => Theme(
      data: ThemeData.dark().copyWith(
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF7B8CDE),
          surface: Color(0xFF1A1A1A),
        ),
      ),
      child: child!,
    ),
  );
  if (date == null) return null;

  final time = await showTimePicker(
    // ignore: use_build_context_synchronously
    context: context,
    initialTime: TimeOfDay.now(),
    builder: (ctx, child) => Theme(
      data: ThemeData.dark().copyWith(
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF7B8CDE),
          surface: Color(0xFF1A1A1A),
        ),
      ),
      child: child!,
    ),
  );
  if (time == null) return null;

  return DateTime(date.year, date.month, date.day, time.hour, time.minute);
}
