import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'providers/auth_provider.dart';

class CalendarView extends ConsumerStatefulWidget {
  const CalendarView({super.key});

  @override
  ConsumerState<CalendarView> createState() => _CalendarViewState();
}

class _CalendarViewState extends ConsumerState<CalendarView> with SingleTickerProviderStateMixin {
  late DateTime _currentMonth;
  late AnimationController _animController;
  int? _hoveredDay;
  int? _selectedDay;
  List<dynamic> _googleEvents = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _currentMonth = DateTime(DateTime.now().year, DateTime.now().month, 1);
    _selectedDay = DateTime.now().day;
    _animController = AnimationController(vsync: this, duration: const Duration(milliseconds: 600));
    _animController.forward();
    _fetchEvents();
  }

  Future<void> _fetchEvents() async {
    final api = ref.read(apiClientProvider);
    final events = await api.fetchCalendarEvents(year: _currentMonth.year, month: _currentMonth.month);
    if (mounted) {
      setState(() {
        _googleEvents = events;
        _isLoading = false;
      });
    }
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  void _nextMonth() {
    setState(() {
      _currentMonth = DateTime(_currentMonth.year, _currentMonth.month + 1, 1);
      _isLoading = true;
      _animController.reset();
      _animController.forward();
      _fetchEvents();
    });
  }

  void _prevMonth() {
    setState(() {
      _currentMonth = DateTime(_currentMonth.year, _currentMonth.month - 1, 1);
      _isLoading = true;
      _animController.reset();
      _animController.forward();
      _fetchEvents();
    });
  }

  void _goToToday() {
    setState(() {
      _currentMonth = DateTime(DateTime.now().year, DateTime.now().month, 1);
      _selectedDay = DateTime.now().day;
      _isLoading = true;
      _animController.reset();
      _animController.forward();
      _fetchEvents();
    });
  }

  Future<void> _showAddEventDialog() async {
    final titleCtrl = TextEditingController();
    final descCtrl = TextEditingController();
    
    DateTime selectedDate = DateTime(_currentMonth.year, _currentMonth.month, _selectedDay ?? 1);
    TimeOfDay selectedTime = const TimeOfDay(hour: 10, minute: 0);

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setStateSB) {
          return AlertDialog(
            backgroundColor: const Color(0xFF131315),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24), side: BorderSide(color: Colors.white.withValues(alpha: 0.1))),
            title: const Text('New Event', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 22)),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(controller: titleCtrl, style: const TextStyle(color: Colors.white), decoration: const InputDecoration(labelText: 'Event Title', labelStyle: TextStyle(color: Colors.white54))),
                const SizedBox(height: 12),
                TextField(controller: descCtrl, style: const TextStyle(color: Colors.white), decoration: const InputDecoration(labelText: 'Description', labelStyle: TextStyle(color: Colors.white54))),
                const SizedBox(height: 24),
                Row(
                  children: [
                    Expanded(
                      child: InkWell(
                        onTap: () async {
                           final d = await showDatePicker(context: ctx, initialDate: selectedDate, firstDate: DateTime(2000), lastDate: DateTime(2100));
                           if (d != null) setStateSB(() => selectedDate = d);
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                          decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.04), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white.withValues(alpha: 0.1))),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Date', style: TextStyle(fontSize: 11, color: Colors.white38)),
                              const SizedBox(height: 4),
                              Text(DateFormat('MMM dd, yyyy').format(selectedDate), style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
                            ],
                          )
                        )
                      )
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: InkWell(
                        onTap: () async {
                           final t = await showTimePicker(context: ctx, initialTime: selectedTime);
                           if (t != null) setStateSB(() => selectedTime = t);
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                          decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.04), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white.withValues(alpha: 0.1))),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Time', style: TextStyle(fontSize: 11, color: Colors.white38)),
                              const SizedBox(height: 4),
                              Text(selectedTime.format(ctx), style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
                            ],
                          )
                        )
                      )
                    )
                  ]
                )
              ]
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel', style: TextStyle(color: Colors.white54))),
              ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: Colors.purpleAccent, foregroundColor: Colors.white, elevation: 0, padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                onPressed: () async {
                  if (titleCtrl.text.isEmpty) return;
                  final start = DateTime(selectedDate.year, selectedDate.month, selectedDate.day, selectedTime.hour, selectedTime.minute);
                  final end = start.add(const Duration(hours: 1)); // Default 1 hour block
                  
                  Navigator.pop(ctx);
                  setState(() => _isLoading = true);
                  try {
                    await ref.read(apiClientProvider).createCalendarEvent(
                       titleCtrl.text, 
                       descCtrl.text, 
                       start.toUtc().toIso8601String(), 
                       end.toUtc().toIso8601String()
                    );
                  } catch (_) {}
                  _fetchEvents();
                }, child: const Text('Save Event')
              )
            ]
          );
        }
      )
    );
  }

  Future<void> _confirmDelete(String eventId) async {
    final act = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1D),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Delete Event?', style: TextStyle(color: Colors.white)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel', style: TextStyle(color: Colors.white54))),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Delete', style: TextStyle(color: Colors.redAccent))),
        ]
      )
    );
    if (act == true) {
      setState(() => _isLoading = true);
      try {
        await ref.read(apiClientProvider).deleteCalendarEvent(eventId);
      } catch (_) {}
      _fetchEvents();
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('Calendar & Agenda', style: TextStyle(
                fontSize: 28, fontWeight: FontWeight.w600,
                letterSpacing: -0.5, color: Colors.white
              )),
              const Spacer(),
              _buildAddEventButton()
            ],
          ),
          const SizedBox(height: 8),
          Text('Your proactive daily schedule managed by the AI.', style: TextStyle(fontSize: 15, color: Colors.grey[500])),
          const SizedBox(height: 32),
          
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                flex: 5,
                child: _buildGlassContainer(
                   child: _buildCalendarGrid(),
                ),
              ),
              const SizedBox(width: 24),
              Expanded(
                flex: 4,
                child: _buildGlassContainer(
                   child: _buildAgendaList(),
                ),
              ),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildCalendarGrid() {
    final daysInMonth = DateUtils.getDaysInMonth(_currentMonth.year, _currentMonth.month);
    final firstDayOffset = _currentMonth.weekday % 7; // Sunday = 0
    
    const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    final monthName = _getMonthName(_currentMonth.month);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Text('$monthName ${_currentMonth.year}', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white)),
                const SizedBox(width: 16),
                InkWell(
                  onTap: _goToToday,
                  borderRadius: BorderRadius.circular(20),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(20)),
                    child: const Text('Today', style: TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.w600)),
                  ),
                )
              ]
            ),
            Row(
              children: [
                _buildIconButton(Icons.chevron_left, _prevMonth),
                const SizedBox(width: 8),
                _buildIconButton(Icons.chevron_right, _nextMonth),
              ],
            )
          ],
        ),
        const SizedBox(height: 24),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: weekDays.map((d) => 
            SizedBox(width: 40, child: Center(child: Text(d, style: const TextStyle(color: Colors.white54, fontWeight: FontWeight.w600, fontSize: 13))))
          ).toList(),
        ),
        const SizedBox(height: 16),
        FadeTransition(
          opacity: _animController,
          child: SlideTransition(
            position: Tween<Offset>(begin: const Offset(0, 0.05), end: Offset.zero).animate(CurvedAnimation(parent: _animController, curve: Curves.easeOutCubic)),
            child: GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 7,
                mainAxisSpacing: 8,
                crossAxisSpacing: 8,
              ),
              itemCount: 42,
              itemBuilder: (context, index) {
                if (index < firstDayOffset || index >= firstDayOffset + daysInMonth) {
                  return const SizedBox();
                }
                final day = index - firstDayOffset + 1;
                final isSelected = _selectedDay == day;
                final isHovered = _hoveredDay == day;
                
                final now = DateTime.now();
                final isToday = day == now.day && _currentMonth.month == now.month && _currentMonth.year == now.year;

                final dayEvents = _googleEvents.where((evt) {
                  final start = evt['start'] as String?;
                  if (start == null) return false;
                  try {
                    final dt = DateTime.parse(start).toLocal();
                    return dt.year == _currentMonth.year && dt.month == _currentMonth.month && dt.day == day;
                  } catch (_) { return false; }
                }).toList();
                
                int dotCount = dayEvents.length > 3 ? 3 : dayEvents.length;

                return MouseRegion(
                  onEnter: (_) => setState(() => _hoveredDay = day),
                  onExit: (_) => setState(() => _hoveredDay = null),
                  child: GestureDetector(
                    onTap: () => setState(() => _selectedDay = day),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      curve: Curves.easeOutCubic,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: isToday && !isSelected ? Border.all(color: Colors.purpleAccent, width: 1.5) : null,
                        gradient: isSelected
                            ? LinearGradient(colors: [Colors.purpleAccent.shade400, Colors.deepPurpleAccent])
                            : isHovered
                                ? LinearGradient(colors: [Colors.white.withValues(alpha: 0.1), Colors.white.withValues(alpha: 0.05)])
                                : null,
                        color: !isSelected && !isHovered ? Colors.transparent : null,
                        boxShadow: isSelected ? [BoxShadow(color: Colors.purpleAccent.withValues(alpha: 0.4), blurRadius: 12, spreadRadius: 2)] : [],
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const SizedBox(height: 4), 
                          Text('$day', style: TextStyle(
                            fontSize: 15, 
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                            color: isSelected ? Colors.white : Colors.white70
                          )),
                          if (dotCount > 0)
                             Row(
                               mainAxisAlignment: MainAxisAlignment.center,
                               children: List.generate(dotCount, (idx) => Container(
                                  margin: const EdgeInsets.only(top: 2, left: 1, right: 1),
                                  width: 4, height: 4,
                                  decoration: BoxDecoration(
                                     color: isSelected ? Colors.white : Colors.purpleAccent,
                                     shape: BoxShape.circle
                                  )
                               ))
                             )
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ),
      ],
    );
  }
  
  Widget _buildAgendaList() {
    final selectedDate = DateTime(_currentMonth.year, _currentMonth.month, _selectedDay ?? 1);
    final dayEvents = _googleEvents.where((evt) {
      final start = evt['start'] as String?;
      if (start == null) return false;
      try {
        final dt = DateTime.parse(start).toLocal();
        return dt.year == selectedDate.year && dt.month == selectedDate.month && dt.day == selectedDate.day;
      } catch (_) {
        return false;
      }
    }).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.flash_on, color: Colors.amberAccent, size: 20),
            const SizedBox(width: 8),
            Text('Agenda for ${_getMonthName(_currentMonth.month)} $_selectedDay', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
          ],
        ),
        const SizedBox(height: 24),
        if (_isLoading)
          const Center(child: CircularProgressIndicator(color: Colors.white24))
        else if (dayEvents.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 32),
            child: Center(child: Text("Schedule clear for today.", style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 15))),
          )
        else
          ...dayEvents.asMap().entries.map((entry) {
             final idx = entry.key;
             final evt = entry.value;
             
             final start = evt['start'] as String;
             String timeStr = "All Day";
             try {
                final dt = DateTime.parse(start).toLocal();
                timeStr = DateFormat('h:mm a').format(dt);
             } catch (_) {}
             final loc = evt['location']?.toString();
             final subtitle = (loc != null && loc.isNotEmpty) ? loc : "Scheduled Event";
             
             final colorChoices = [Colors.greenAccent, Colors.blueAccent, Colors.purpleAccent, Colors.orangeAccent];
             final color = colorChoices[evt['summary'].hashCode % colorChoices.length];

             return TweenAnimationBuilder<double>(
               key: ValueKey(evt['id']),
               tween: Tween(begin: 0.0, end: 1.0),
               duration: Duration(milliseconds: 400 + (idx * 150)),
               curve: Curves.easeOutCubic,
               builder: (context, val, child) {
                 return Opacity(
                   opacity: val,
                   child: Transform.translate(
                     offset: Offset(0, 30 * (1 - val)),
                     child: child,
                   ),
                 );
               },
               child: _buildTimelineEventCard(evt['id'] as String, timeStr, evt['summary'] ?? 'Event', subtitle, color, idx == dayEvents.length - 1),
             );
          }),
      ],
    );
  }

  Widget _buildTimelineEventCard(String eventId, String time, String title, String subtitle, Color stripColor, bool isLast) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Timeline Stem
          SizedBox(
            width: 40,
            child: Column(
              children: [
                Container(
                  width: 14, height: 14,
                  margin: const EdgeInsets.only(top: 8),
                  decoration: BoxDecoration(
                     color: stripColor.withValues(alpha: 0.2), 
                     border: Border.all(color: stripColor, width: 2),
                     shape: BoxShape.circle,
                     boxShadow: [BoxShadow(color: stripColor.withValues(alpha: 0.5), blurRadius: 10)]
                  )
                ),
                if (!isLast)
                Expanded(
                  child: Container(
                    width: 2,
                    margin: const EdgeInsets.only(top: 4, bottom: 4),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter, end: Alignment.bottomCenter,
                        colors: [stripColor.withValues(alpha: 0.5), Colors.white.withValues(alpha: 0.05), Colors.white.withValues(alpha: 0.0)]
                      )
                    )
                  )
                )
              ]
            )
          ),
          const SizedBox(width: 4),
          // Agenda Payload Card
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 24),
              child: MouseRegion(
                cursor: SystemMouseCursors.click,
                child: GestureDetector(
                  onLongPress: () => _confirmDelete(eventId),
                  onDoubleTap: () => _confirmDelete(eventId),
                  child: TweenAnimationBuilder<double>(
                    duration: const Duration(milliseconds: 200),
                    tween: Tween(begin: 1.0, end: 1.0),
                    builder: (context, scale, child) {
                      return Transform.scale(scale: scale, child: child);
                    },
                    child: Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.03),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Colors.white)),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    Icon(Icons.schedule, size: 12, color: stripColor),
                                    const SizedBox(width: 6),
                                    Text(time, style: TextStyle(fontSize: 12, color: Colors.white.withValues(alpha: 0.9), fontWeight: FontWeight.bold)),
                                    const SizedBox(width: 12),
                                    Icon(Icons.location_on_outlined, size: 12, color: Colors.white.withValues(alpha: 0.4)),
                                    const SizedBox(width: 4),
                                    Text(subtitle, style: const TextStyle(fontSize: 12, color: Colors.white54)),
                                  ],
                                )
                              ],
                            ),
                          ),
                          Icon(Icons.more_vert, size: 16, color: Colors.white.withValues(alpha: 0.2)),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          )
        ],
      )
    );
  }

  Widget _buildGlassContainer({required Widget child}) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          padding: const EdgeInsets.all(32),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.03),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08), width: 1.5),
            boxShadow: [
              BoxShadow(color: Colors.black.withValues(alpha: 0.2), blurRadius: 30, spreadRadius: -5),
            ],
          ),
          child: child,
        ),
      ),
    );
  }

  Widget _buildIconButton(IconData icon, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
        ),
        child: Icon(icon, size: 18, color: Colors.white70),
      ),
    );
  }

  Widget _buildAddEventButton() {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        gradient: LinearGradient(colors: [Colors.purpleAccent.shade400, Colors.deepPurpleAccent]),
        boxShadow: [BoxShadow(color: Colors.deepPurpleAccent.withValues(alpha: 0.3), blurRadius: 12, offset: const Offset(0, 4))],
      ),
      child: ElevatedButton.icon(
        onPressed: _showAddEventDialog,
        icon: const Icon(Icons.add, size: 16, color: Colors.white),
        label: const Text('Add Event', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
    );
  }

  String _getMonthName(int month) {
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    return months[month - 1];
  }
}
