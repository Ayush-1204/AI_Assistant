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
class _JobCard extends ConsumerWidget {
  final Map<String, dynamic> job;
  const _JobCard({required this.job});

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

  IconData _statusIcon(String status) {
    switch (status.toUpperCase()) {
      case 'PENDING':
        return Icons.schedule;
      case 'RUNNING':
        return Icons.play_circle_outline;
      case 'COMPLETED':
        return Icons.check_circle_outline;
      case 'FAILED':
        return Icons.error_outline;
      default:
        return Icons.radio_button_unchecked;
    }
  }

  String _formatDateTime(String? iso) {
    if (iso == null) return '—';
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
  Widget build(BuildContext context, WidgetRef ref) {
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
      child: Container(
        margin: const EdgeInsets.only(bottom: 14),
        decoration: BoxDecoration(
          color: const Color(0xFF151515),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: isEnabled
                ? Colors.white.withValues(alpha: 0.08)
                : Colors.white.withValues(alpha: 0.03),
          ),
          boxShadow: isEnabled
              ? [
                  BoxShadow(
                    color: color.withValues(alpha: 0.04),
                    blurRadius: 16,
                    spreadRadius: 1,
                  )
                ]
              : [],
        ),
        child: AnimatedOpacity(
          duration: const Duration(milliseconds: 250),
          opacity: isEnabled ? 1.0 : 0.5,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top row
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 16, 14, 10),
                child: Row(
                  children: [
                    // Status indicator
                    Container(
                      padding: const EdgeInsets.all(7),
                      decoration: BoxDecoration(
                        color: color.withValues(alpha: 0.1),
                        shape: BoxShape.circle,
                        border: Border.all(color: color.withValues(alpha: 0.3)),
                      ),
                      child: Icon(_statusIcon(status), size: 14, color: color),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            job['label'] as String? ?? 'Unnamed Job',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Row(
                            children: [
                              if (isCron) ...[
                                Icon(Icons.repeat,
                                    size: 11,
                                    color: Colors.white.withValues(alpha: 0.35)),
                                const SizedBox(width: 3),
                                Text(
                                  job['cron_expression'] as String,
                                  style: TextStyle(
                                    color: Colors.white.withValues(alpha: 0.35),
                                    fontSize: 11,
                                    fontFamily: 'monospace',
                                  ),
                                ),
                              ] else ...[
                                Icon(Icons.calendar_today,
                                    size: 11,
                                    color: Colors.white.withValues(alpha: 0.35)),
                                const SizedBox(width: 3),
                                Text(
                                  'One-shot',
                                  style: TextStyle(
                                    color: Colors.white.withValues(alpha: 0.35),
                                    fontSize: 11,
                                  ),
                                ),
                              ],
                              const SizedBox(width: 10),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 6, vertical: 1),
                                decoration: BoxDecoration(
                                  color: color.withValues(alpha: 0.1),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  status,
                                  style: TextStyle(
                                    color: color,
                                    fontSize: 9,
                                    fontWeight: FontWeight.bold,
                                    letterSpacing: 0.5,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    // Toggle switch
                    Switch.adaptive(
                      value: isEnabled,
                      onChanged: (_) =>
                          ref.read(scheduledJobsProvider.notifier).toggle(job['id'] as int),
                      activeColor: const Color(0xFF7B8CDE),
                      inactiveThumbColor: Colors.white30,
                      inactiveTrackColor: Colors.white10,
                    ),
                    // Delete
                    IconButton(
                      icon: const Icon(Icons.delete_outline,
                          size: 18, color: Colors.white30),
                      onPressed: () async {
                        final confirm = await showDialog<bool>(
                          context: context,
                          builder: (ctx) => AlertDialog(
                            backgroundColor: const Color(0xFF1B1B1B),
                            title: const Text('Delete Job',
                                style: TextStyle(color: Colors.white)),
                            content: Text(
                              'Delete "${job['label']}"? This cannot be undone.',
                              style: TextStyle(color: Colors.white.withValues(alpha: 0.6)),
                            ),
                            actions: [
                              TextButton(
                                onPressed: () => Navigator.pop(ctx, false),
                                child: const Text('Cancel',
                                    style: TextStyle(color: Colors.white54)),
                              ),
                              ElevatedButton(
                                onPressed: () => Navigator.pop(ctx, true),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.redAccent.withValues(alpha: 0.2),
                                ),
                                child: const Text('Delete',
                                    style: TextStyle(color: Colors.redAccent)),
                              ),
                            ],
                          ),
                        );
                        if (confirm == true) {
                          ref.read(scheduledJobsProvider.notifier).delete(job['id'] as int);
                        }
                      },
                    ),
                  ],
                ),
              ),

              // Directive
              if (job['directive'] != null)
                Padding(
                  padding: const EdgeInsets.fromLTRB(18, 0, 18, 10),
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.03),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
                    ),
                    child: Text(
                      job['directive'] as String,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.5),
                        fontSize: 12,
                        height: 1.4,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),

              // Footer: next run
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 0, 18, 14),
                child: Row(
                  children: [
                    Icon(Icons.access_time,
                        size: 12, color: Colors.white.withValues(alpha: 0.25)),
                    const SizedBox(width: 5),
                    Text(
                      'Next: ${_formatDateTime(job['next_run_at'] as String? ?? job['scheduled_time'] as String?)}',
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.25),
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// EMPTY STATE
// ─────────────────────────────────────────────────────────────────────────────
class _EmptyState extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: const Color(0xFF7B8CDE).withValues(alpha: 0.08),
              shape: BoxShape.circle,
              border: Border.all(
                  color: const Color(0xFF7B8CDE).withValues(alpha: 0.2)),
            ),
            child: const Icon(Icons.schedule_outlined,
                size: 36, color: Color(0xFF7B8CDE)),
          ),
          const SizedBox(height: 20),
          const Text(
            'No Scheduled Jobs',
            style: TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Create standing agent instructions that run\nautomatically on a schedule.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.4),
              fontSize: 13,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 28),
          _NewJobButton(),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// NEW JOB BUTTON & DIALOG
// ─────────────────────────────────────────────────────────────────────────────
class _NewJobButton extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ElevatedButton.icon(
      onPressed: () => _showNewJobDialog(context, ref),
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

  void _showNewJobDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (ctx) => _NewJobDialog(
        onCreate: ({
          required String label,
          required String directive,
          String? cronExpression,
          DateTime? runAt,
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
  }
}

class _NewJobDialog extends StatefulWidget {
  final Future<void> Function({
    required String label,
    required String directive,
    String? cronExpression,
    DateTime? runAt,
  }) onCreate;

  const _NewJobDialog({required this.onCreate});

  @override
  State<_NewJobDialog> createState() => _NewJobDialogState();
}

class _NewJobDialogState extends State<_NewJobDialog> {
  final _labelCtrl = TextEditingController();
  final _directiveCtrl = TextEditingController();
  bool _isCron = true;
  bool _isLoading = false;
  DateTime? _runAt;
  String _repeat = 'Daily';
  String _time = 'Morning';
  String? _error;

  @override
  void dispose() {
    _labelCtrl.dispose();
    _directiveCtrl.dispose();
    super.dispose();
  }

  String _generateCron() {
    String hour = '8';
    switch (_time) {
      case 'Morning': hour = '8'; break;
      case 'Afternoon': hour = '14'; break;
      case 'Evening': hour = '20'; break;
      case 'Midnight': hour = '0'; break;
    }
    
    switch (_repeat) {
      case 'Daily': return '0 $hour * * *';
      case 'Weekly': return '0 $hour * * 1';
      case 'Monthly': return '0 $hour 1 * *';
      default: return '0 $hour * * *';
    }
  }

  String _computeNextRunStr() {
    final now = DateTime.now();
    int hour = 8;
    switch (_time) {
      case 'Morning': hour = 8; break;
      case 'Afternoon': hour = 14; break;
      case 'Evening': hour = 20; break;
      case 'Midnight': hour = 0; break;
    }

    DateTime next;
    if (_repeat == 'Daily') {
      next = DateTime(now.year, now.month, now.day, hour);
      if (next.isBefore(now)) next = next.add(const Duration(days: 1));
    } else if (_repeat == 'Weekly') {
      next = DateTime(now.year, now.month, now.day, hour);
      while (next.weekday != DateTime.monday || next.isBefore(now)) {
        next = next.add(const Duration(days: 1));
      }
    } else {
      next = DateTime(now.year, now.month, 1, hour);
      if (next.isBefore(now)) {
        next = DateTime(now.year, now.month + 1, 1, hour);
      }
    }

    final today = DateTime(now.year, now.month, now.day);
    final nextDay = DateTime(next.year, next.month, next.day);
    
    String dayStr;
    if (nextDay == today) {
      dayStr = 'Today';
    } else if (nextDay == today.add(const Duration(days: 1))) {
      dayStr = 'Tomorrow';
    } else {
      final months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      dayStr = '${months[next.month - 1]} ${next.day}';
    }

    final h = hour == 0 ? 12 : (hour > 12 ? hour - 12 : hour);
    final ampm = hour < 12 ? 'AM' : 'PM';
    return '$dayStr at $h:00 $ampm';
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

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      await widget.onCreate(
        label: label,
        directive: directive,
        cronExpression: _isCron ? _generateCron() : null,
        runAt: _isCron ? null : _runAt,
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
              // Title
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: const Color(0xFF7B8CDE).withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.add_alarm,
                        color: Color(0xFF7B8CDE), size: 20),
                  ),
                  const SizedBox(width: 12),
                  const Text(
                    'New Scheduled Job',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Label
              _FieldLabel('Job Name'),
              const SizedBox(height: 6),
              _buildTextField(_labelCtrl, 'e.g. Weekly Summary Email'),
              const SizedBox(height: 16),

              // Directive
              _FieldLabel('Agent Directive'),
              const SizedBox(height: 6),
              _buildTextField(
                _directiveCtrl,
                'What should the agent do? e.g. Summarize my week and email it to me.',
                maxLines: 3,
              ),
              const SizedBox(height: 16),

              // Type toggle
              Row(
                children: [
                  _TypeChip(
                    label: 'Recurring (Cron)',
                    icon: Icons.repeat,
                    selected: _isCron,
                    onTap: () => setState(() => _isCron = true),
                  ),
                  const SizedBox(width: 8),
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
                _buildDropdown('Repeat', _repeat, ['Daily', 'Weekly', 'Monthly'], (v) {
                  if (v != null) setState(() => _repeat = v);
                }),
                _buildDropdown('Time', _time, ['Morning', 'Afternoon', 'Evening', 'Midnight'], (v) {
                  if (v != null) setState(() => _time = v);
                }),
                _buildDropdown('End repeat', 'Never', ['Never'], (v) {}),
                
                // Next run display
                Container(
                  margin: const EdgeInsets.only(top: 8),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.02),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Next run', style: TextStyle(color: Colors.white.withValues(alpha: 0.8), fontSize: 13, fontWeight: FontWeight.w500)),
                      Text(_computeNextRunStr(), style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 13)),
                    ],
                  ),
                ),
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
                    padding: const EdgeInsets.symmetric(
                        horizontal: 14, vertical: 12),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.04),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                          color: Colors.white.withValues(alpha: 0.08)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.calendar_today,
                            size: 14, color: Colors.white54),
                        const SizedBox(width: 8),
                        Text(
                          _runAt == null
                              ? 'Pick a date and time…'
                              : _runAt.toString().substring(0, 16),
                          style: TextStyle(
                            color: _runAt == null
                                ? Colors.white30
                                : Colors.white,
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
                    border: Border.all(
                        color: Colors.redAccent.withValues(alpha: 0.3)),
                  ),
                  child: Text(_error!,
                      style: const TextStyle(
                          color: Colors.redAccent, fontSize: 12)),
                ),
              ],

              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('Cancel',
                        style: TextStyle(color: Colors.white54)),
                  ),
                  const SizedBox(width: 10),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _submit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF7B8CDE),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10)),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 20, vertical: 12),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white))
                        : const Text('Create Job',
                            style: TextStyle(fontWeight: FontWeight.w600)),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTextField(TextEditingController ctrl, String hint,
      {int maxLines = 1, String? fontFamily}) {
    return TextField(
      controller: ctrl,
      maxLines: maxLines,
      style: TextStyle(
          color: Colors.white, fontSize: 13, fontFamily: fontFamily),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: TextStyle(
            color: Colors.white.withValues(alpha: 0.25), fontSize: 13),
        filled: true,
        fillColor: Colors.white.withValues(alpha: 0.04),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.08)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.08)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: Color(0xFF7B8CDE)),
        ),
      ),
    );
  }

  Widget _buildDropdown(String label, String value, List<String> items, ValueChanged<String?> onChanged) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.8), fontSize: 13, fontWeight: FontWeight.w500)),
          DropdownButton<String>(
            value: value,
            underline: const SizedBox(),
            dropdownColor: const Color(0xFF222222),
            icon: const Icon(Icons.keyboard_arrow_down, size: 16, color: Colors.white54),
            style: const TextStyle(color: Colors.white, fontSize: 13),
            items: items.map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
            onChanged: onChanged,
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
