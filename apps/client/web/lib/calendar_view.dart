import 'dart:async';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'providers/auth_provider.dart';

// ─── Event color palette (cycles by hash) ─────────────────────────────────
const _kEventColors = [
  Color(0xFF039BE5), // Google Blue
  Color(0xFFD50000), // Google Red
  Color(0xFFF4511E), // Google Orange
  Color(0xFF8E24AA), // Google Purple
  Color(0xFF0B8043), // Google Green
];

Color _eventColor(String? summary) {
  if (summary == null || summary.isEmpty) return _kEventColors[0];
  return _kEventColors[(summary.hashCode.abs()) % _kEventColors.length];
}

// Returns true when start is a date-only string ("2026-07-31", 10 chars)
bool _isDateOnly(dynamic event) {
  final s = event['start'] as String?;
  if (s == null) return false;
  return s.length == 10; // "YYYY-MM-DD" with no time component
}

bool _isAllDay(dynamic event) {
  if (_isDateOnly(event)) return true;
  final s = event['start'] as String?;
  final e = event['end'] as String?;
  if (s != null && e != null) {
    try {
      final startDt = DateTime.parse(s).toLocal();
      final endDt = DateTime.parse(e).toLocal();
      return startDt.year != endDt.year || startDt.month != endDt.month || startDt.day != endDt.day;
    } catch (_) {}
  }
  return false;
}

bool _isBirthday(dynamic event) {
  final s = (event['summary'] as String? ?? '').toLowerCase();
  return s.contains('birthday') || s.contains('birt...');
}

// ─── View enum ─────────────────────────────────────────────────────────────
enum CalView { day, week, month }

// ───────────────────────────────────────────────────────────────────────────
class CalendarView extends ConsumerStatefulWidget {
  const CalendarView({super.key});

  @override
  ConsumerState<CalendarView> createState() => _CalendarViewState();
}

class _CalendarViewState extends ConsumerState<CalendarView>
    with TickerProviderStateMixin {
  CalView _view = CalView.month;
  late DateTime _focusDate; // selected day / week anchor / month anchor
  Map<String, dynamic> _events = {};
  final Set<String> _loadedMonths = {};
  bool _isLoading = true;
  bool _isFirstLoad = true;
  int _slideDir = 1;

  late AnimationController _fadeCtrl;
  ScrollController? _timeGridScrollCtrl;
  
  Timer? _debounceTimer;

  late PageController _weekPageCtrl;
  late PageController _dayPageCtrl;

  // Month view: true bidirectional infinite CustomScrollView
  final GlobalKey _monthCenterKey = GlobalKey();
  final ScrollController _monthScrollCtrl = ScrollController();
  double _monthRowH = 0;
  bool _isSnapping = false;
  
  final DateTime _anchorDate = DateTime(DateTime.now().year, DateTime.now().month, DateTime.now().day);
  
  int _daysBetween(DateTime a, DateTime b) {
    return DateTime.utc(b.year, b.month, b.day)
        .difference(DateTime.utc(a.year, a.month, a.day))
        .inDays;
  }

  int _calcWeekIdx(DateTime d) {
    final startNow = _anchorDate.subtract(Duration(days: _anchorDate.weekday - 1));
    final startTarget = d.subtract(Duration(days: d.weekday - 1));
    return 10000 + (_daysBetween(startNow, startTarget) / 7).round();
  }
  int _calcDayIdx(DateTime d) => 10000 + _daysBetween(_anchorDate, d);


  @override
  void initState() {
    super.initState();
    _focusDate = DateTime.now();
    _fadeCtrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 400));
        
    final now = DateTime.now();
    final hourPixels = (now.hour * 60.0 + now.minute) / 60.0 * 60.0;
    _timeGridScrollCtrl = ScrollController(
        initialScrollOffset: (hourPixels - 300).clamp(0.0, double.infinity));
        
    _weekPageCtrl = PageController(initialPage: _calcWeekIdx(_focusDate));
    _dayPageCtrl = PageController(initialPage: _calcDayIdx(_focusDate));
        
    _fetchEvents();
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _fadeCtrl.dispose();
    _timeGridScrollCtrl?.dispose();
    _weekPageCtrl.dispose();
    _dayPageCtrl.dispose();
    _monthScrollCtrl.dispose();
    super.dispose();
  }

  // ── Data fetching ────────────────────────────────────────────────────────
  void _fetchEventsDebounced() {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 250), () {
      if (mounted) _fetchEvents();
    });
  }

  Future<void> _fetchEvents({bool force = false}) async {
    final monthKey = '-';
    
    if (!force && _loadedMonths.contains(monthKey)) {
      if (_isFirstLoad && mounted) {
        setState(() => _isFirstLoad = false);
        _fadeCtrl.forward();
      }
      return;
    }

    // Only show spinner on very first load
    if (_isFirstLoad && mounted) {
      setState(() => _isLoading = true);
      _fadeCtrl.reset();
    }

    try {
      final api = ref.read(apiClientProvider);
      final evts = await api.fetchCalendarEvents(
          year: _focusDate.year, month: _focusDate.month);

      if (mounted) {
        _loadedMonths.add(monthKey);
        setState(() {
          for (var evt in evts) {
            if (evt['id'] != null) {
              _events[evt['id'].toString()] = evt;
            }
          }
          _isLoading = false;
        });
        if (_isFirstLoad) {
          _isFirstLoad = false;
          _fadeCtrl.forward();
        }
      }
    } catch (_) {
      if (mounted) {
        setState(() {
           _isLoading = false;
           _isFirstLoad = false;
        });
      }
    }
  }

  // ── Navigation ─────────────────────────────────────────────────────────
  // IMPORTANT: Never call setState() in goNext/goPrev.
  // The PageController animates the page; onPageChanged() updates _focusDate.
  // Calling setState here would rebuild the widget tree and reset the scroll.
  void _goNext() {
    switch (_view) {
      case CalView.day:
        _dayPageCtrl.nextPage(
            duration: const Duration(milliseconds: 220), curve: Curves.easeOut);
        break;
      case CalView.week:
        _weekPageCtrl.nextPage(
            duration: const Duration(milliseconds: 220), curve: Curves.easeOut);
        break;
      case CalView.month:
        final nextMonth = DateTime(_focusDate.year, _focusDate.month + 1, 1);
        _jumpToDate(nextMonth);
        break;
    }
  }

  void _goPrev() {
    switch (_view) {
      case CalView.day:
        _dayPageCtrl.previousPage(
            duration: const Duration(milliseconds: 220), curve: Curves.easeOut);
        break;
      case CalView.week:
        _weekPageCtrl.previousPage(
            duration: const Duration(milliseconds: 220), curve: Curves.easeOut);
        break;
      case CalView.month:
        final prevMonth = DateTime(_focusDate.year, _focusDate.month - 1, 1);
        _jumpToDate(prevMonth);
        break;
    }
  }

  void _goToday() {
    _jumpToDate(DateTime.now());
  }

  void _jumpToDate(DateTime d) {
    setState(() => _focusDate = d);
    // Month view: compute pixel offset from anchor to target month
    if (_monthScrollCtrl.hasClients && _monthRowH > 0) {
      final targetFirst = DateTime(d.year, d.month, 1);
      final anchorSunday = _anchorDate.subtract(Duration(days: _anchorDate.weekday % 7));
      final daysDiff = targetFirst.difference(anchorSunday).inDays;
      final weekOffset = (daysDiff / 7.0).floorToDouble(); 
      _monthScrollCtrl.animateTo(
        weekOffset * _monthRowH,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
    if (_weekPageCtrl.hasClients) {
      _weekPageCtrl.animateToPage(_calcWeekIdx(d),
          duration: const Duration(milliseconds: 120), curve: Curves.easeOut);
    }
    if (_dayPageCtrl.hasClients) {
      _dayPageCtrl.animateToPage(_calcDayIdx(d),
          duration: const Duration(milliseconds: 120), curve: Curves.easeOut);
    }
    _fetchEventsDebounced();
  }

  // ── Events for a given date ──────────────────────────────────────────────
  List<dynamic> _eventsForDate(DateTime date) {
    return _events.values.where((e) {
      // All-day events: use _eventSpansDay which handles date-only strings
      if (_isAllDay(e)) return _eventSpansDay(e, date);

      final start = e['start'] as String?;
      if (start == null) return false;
      try {
        final dtStart = DateTime.parse(start).toLocal();
        final dtStartDay = DateTime(dtStart.year, dtStart.month, dtStart.day);
        
        final end = e['end'] as String?;
        DateTime dtEndDay = dtStartDay;
        if (end != null) {
          final dtEnd = DateTime.parse(end).toLocal();
          dtEndDay = DateTime(dtEnd.year, dtEnd.month, dtEnd.day);
          // If the event ends at midnight (00:00:00) the next day, it should not render on the next day's square.
          if (dtEnd.hour == 0 && dtEnd.minute == 0 && dtEnd.second == 0 && dtEnd.isAfter(dtStart)) {
             dtEndDay = dtEndDay.subtract(const Duration(days: 1));
          }
        }
        
        final target = DateTime(date.year, date.month, date.day);
        return (target.isAtSameMomentAs(dtStartDay) || target.isAfter(dtStartDay)) &&
               (target.isAtSameMomentAs(dtEndDay) || target.isBefore(dtEndDay));
      } catch (_) {
        return false;
      }
    }).toList();
  }

  // ── Add event dialog ─────────────────────────────────────────────────────
  void _showEventSummary(BuildContext context, dynamic event) {
    showDialog(
      context: context,
      builder: (ctx) => Dialog(
        backgroundColor: Colors.transparent,
        child: Container(
          width: 400,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFF161618),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.white.withOpacity(0.08), width: 1.5),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.5),
                blurRadius: 32,
                offset: const Offset(0, 16),
              )
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  IconButton(
                    icon: const Icon(Icons.edit, color: Colors.white70, size: 20),
                    onPressed: () {
                      // TODO: Implement actual edit flow
                      Navigator.pop(ctx);
                    },
                    hoverColor: Colors.white.withOpacity(0.1),
                    splashRadius: 20,
                  ),
                  IconButton(
                    icon: const Icon(Icons.delete, color: Colors.white70, size: 20),
                    onPressed: () {
                      Navigator.pop(ctx);
                      _confirmDelete(event['id']);
                    },
                    hoverColor: Colors.white.withOpacity(0.1),
                    splashRadius: 20,
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.white70, size: 20),
                    onPressed: () => Navigator.pop(ctx),
                    hoverColor: Colors.white.withOpacity(0.1),
                    splashRadius: 20,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 16,
                    height: 16,
                    margin: const EdgeInsets.only(top: 4, right: 12),
                    decoration: BoxDecoration(
                      color: _eventColor(event['summary']),
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          event['summary'] ?? 'No Title',
                          style: const TextStyle(fontSize: 22, color: Colors.white, fontWeight: FontWeight.w500),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'From: \nTo: ',
                          style: const TextStyle(fontSize: 14, color: Colors.white70),
                        ),
                      ],
                    ),
                  )
                ],
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showAddEventDialog([DateTime? preselected]) async {
    final selDate = preselected ?? _focusDate;
    final selTime = const TimeOfDay(hour: 10, minute: 0);

    await showDialog(
      context: context,
      builder: (ctx) => _RichAddEventDialog(
        initialDate: selDate,
        initialTime: selTime,
        onSave: (title, desc, start, end, allDay) async {
          Navigator.pop(ctx);
          setState(() => _isLoading = true);
          try {
            await ref.read(apiClientProvider).createCalendarEvent(
                  title,
                  desc,
                  start.toUtc().toIso8601String(),
                  end.toUtc().toIso8601String(),
                );
          } catch (_) {}
          _fetchEvents(force: true);
        },
      ),
    );
  }

  Future<void> _confirmDelete(String eventId) async {
    final act = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1D),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title:
            const Text('Delete Event?', style: TextStyle(color: Colors.white)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child:
                  const Text('Cancel', style: TextStyle(color: Colors.white54))),
          TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Delete',
                  style: TextStyle(color: Colors.redAccent))),
        ],
      ),
    );
    if (act == true) {
      setState(() => _isLoading = true);
      try {
        await ref.read(apiClientProvider).deleteCalendarEvent(eventId);
      } catch (_) {}
      _fetchEvents(force: true);
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // BUILD
  // ─────────────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(child: _buildMainColumn()),
        _buildRightSidebar(),
      ],
    );
  }

  // ── Main column (header + grid) ──────────────────────────────────────────
  Widget _buildMainColumn() {
    final String currentKey = '$_view';
    return Column(children: [
      _buildTopBar(),
      Expanded(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: _isFirstLoad
              ? const Center(
                  child: CircularProgressIndicator(
                      color: Colors.white24, strokeWidth: 1.5))
              : AnimatedSwitcher(
                  duration: const Duration(milliseconds: 150),
                  switchInCurve: Curves.easeOut,
                  switchOutCurve: Curves.easeIn,
                  transitionBuilder: (child, animation) {
                    final isIncoming = (child.key as ValueKey<String>).value == currentKey;
                    final offsetTween = Tween<Offset>(
                      begin: Offset(isIncoming ? _slideDir * 0.05 : -_slideDir * 0.05, 0),
                      end: Offset.zero,
                    );
                    return FadeTransition(
                      opacity: animation,
                      child: SlideTransition(
                        position: offsetTween.animate(animation),
                        child: child,
                      ),
                    );
                  },
                  child: KeyedSubtree(
                    key: ValueKey(currentKey),
                    child: _buildCurrentView(),
                  ),
                ),
        ),
      ),
    ]);
  }

  // ── Top bar ──────────────────────────────────────────────────────────────
  Widget _buildTopBar() {
    final title = _viewTitle();
    return Container(
      height: 64,
      padding: const EdgeInsets.symmetric(horizontal: 24),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.white.withValues(alpha: 0.07))),
      ),
      child: Row(children: [
        _todayBtn(),
        const SizedBox(width: 12),
        _navBtn(Icons.chevron_left, _goPrev),
        const SizedBox(width: 4),
        _navBtn(Icons.chevron_right, _goNext),
        const SizedBox(width: 16),
        MouseRegion(
          cursor: SystemMouseCursors.click,
          child: GestureDetector(
            onTap: () async {
              final d = await showDatePicker(
                context: context,
                initialDate: _focusDate,
                firstDate: DateTime(2000),
                lastDate: DateTime(2100),
                builder: (context, child) {
                  return Theme(
                    data: ThemeData.dark().copyWith(
                      colorScheme: const ColorScheme.dark(
                        primary: Colors.white,
                        onPrimary: Colors.black,
                        surface: Color(0xFF1E1E1E),
                        onSurface: Colors.white,
                      ),
                    ),
                    child: child!,
                  );
                },
              );
              if (d != null) {
                setState(() => _focusDate = d);
                _jumpToDate(d);
                _fetchEventsDebounced();
              }
            },
            child: Row(
              children: [
                Text(title,
                    style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                        letterSpacing: -0.5)),
                const SizedBox(width: 8),
                 Icon(Icons.arrow_drop_down, size: 20, color: Colors.white.withValues(alpha: 0.5)),
              ],
            ),
          ),
        ),
        const Spacer(),
        _viewToggle(),
        const SizedBox(width: 16),
        _addEventBtn(),
      ]),
    );
  }

  String _viewTitle() {
    switch (_view) {
      case CalView.day:
        return DateFormat('EEEE, MMMM d, yyyy').format(_focusDate);
      case CalView.week:
        final weekStart =
            _focusDate.subtract(Duration(days: _focusDate.weekday - 1));
        final weekEnd = weekStart.add(const Duration(days: 6));
        if (weekStart.month == weekEnd.month) {
          return '${DateFormat('MMMM d').format(weekStart)} – ${DateFormat('d, yyyy').format(weekEnd)}';
        }
        return '${DateFormat('MMM d').format(weekStart)} – ${DateFormat('MMM d, yyyy').format(weekEnd)}';
      case CalView.month:
        return DateFormat('MMMM yyyy').format(_focusDate);
    }
  }

  Widget _navBtn(IconData icon, VoidCallback onTap) => _BouncyButton(
        onTap: onTap,
        child: Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          ),
          child: Icon(icon, size: 18, color: Colors.white60),
        ),
      );

  Widget _todayBtn() => _BouncyButton(
        onTap: _goToday,
        child: Container(
          padding:
              const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Colors.white.withValues(alpha: 0.15)),
          ),
          child: const Text('Today',
              style: TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                  fontWeight: FontWeight.w500)),
        ),
      );

  Widget _viewToggle() {
    return _SegmentedToggle(
      currentView: _view,
      onChanged: (v) {
        if (_view != v) {
          setState(() => _view = v);
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (v == CalView.day && _dayPageCtrl.hasClients) {
              _dayPageCtrl.jumpToPage(_calcDayIdx(_focusDate));
            } else if (v == CalView.week && _weekPageCtrl.hasClients) {
              _weekPageCtrl.jumpToPage(_calcWeekIdx(_focusDate));
            } else if (v == CalView.month) {
              _jumpToDate(_focusDate);
            }
          });
        }
      },
    );
  }

  Widget _addEventBtn() => _BouncyButton(
        onTap: () => _showAddEventDialog(),
        child: Container(
          padding:
              const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: Colors.white.withValues(alpha: 0.15),
                width: 0.5),
          ),
          child: const Row(children: [
            Icon(Icons.add, size: 16, color: Colors.white),
            SizedBox(width: 6),
            Text('New Event',
                style: TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                    fontWeight: FontWeight.w500)),
          ]),
        ),
      );

  // ── Dispatch to view ─────────────────────────────────────────────────────
  Widget _buildCurrentView() {
    switch (_view) {
      case CalView.month:
        return _buildMonthView();
      case CalView.week:
        return _buildWeekView();
      case CalView.day:
        return _buildDayView();
    }
  }

  // ████████████████████████  MONTH VIEW  ████████████████████████████████████

  /// Returns the starting Sunday of a given week offset from _anchorDate
  DateTime _weekStartForOffset(int weekOffset) {
    final anchorSunday = _anchorDate.subtract(Duration(days: _anchorDate.weekday % 7));
    return anchorSunday.add(Duration(days: weekOffset * 7));
  }

  /// Handler for the CustomScrollView's NotificationListener.
  bool _onMonthScroll(ScrollNotification n) {
    if (n is ScrollUpdateNotification) {
      // Determine which month is most visible and update _focusDate
      final offset = _monthScrollCtrl.offset;
      final weekOffset = (offset / _monthRowH).round() + 2;
      final currentSun = _weekStartForOffset(weekOffset);
      // The "focus date" for fetching events is set to the middle of the most visible week
      final midWeek = currentSun.add(const Duration(days: 3));
      if (midWeek.year != _focusDate.year || midWeek.month != _focusDate.month) {
        setState(() => _focusDate = DateTime(midWeek.year, midWeek.month, 1));
        _fetchEventsDebounced();
      }
    }
    if (n is ScrollEndNotification && !_isSnapping) {
      final offset = _monthScrollCtrl.offset;
      final snapped = (offset / _monthRowH).round() * _monthRowH;
      if ((offset - snapped).abs() > 0.5) {
        _isSnapping = true;
        _monthScrollCtrl
            .animateTo(snapped,
                duration: const Duration(milliseconds: 200),
                curve: Curves.easeOut)
            .then((_) => _isSnapping = false);
      }
    }
    return false;
  }

  /// Build one week row for the continuous month view.
  Widget _buildWeekRow(int weekOffset, double rowH) {
    final sun = _weekStartForOffset(weekOffset);
    final now = DateTime.now();

    return SizedBox(
      height: rowH,
      child: Row(
        children: List.generate(7, (i) {
          final cellDate = sun.add(Duration(days: i));
          final isToday = DateUtils.isSameDay(cellDate, now);
          final isSelected = DateUtils.isSameDay(cellDate, _focusDate);
          final isWeekend = cellDate.weekday == DateTime.saturday || cellDate.weekday == DateTime.sunday;
          
          // Show the month name if it's the 1st of the month (or top left cell)
          String? monthName;
          if (cellDate.day == 1 || (weekOffset == 0 && i == 0)) {
            monthName = DateFormat('MMM').format(cellDate);
          }

          // In continuous mode, slightly mute days not in focus month
          final isOutsideMonth = cellDate.month != _focusDate.month;

          return Expanded(
            child: _MonthCell(
              key: ValueKey('${cellDate.toIso8601String()}'),
              cellDate: cellDate,
              monthName: monthName,
              isToday: isToday,
              isSelected: isSelected,
              isWeekend: isWeekend,
              isOutsideMonth: isOutsideMonth,
              events: _eventsForDate(cellDate),
              onTap: () => setState(() => _focusDate = cellDate),
              onAddTap: () => _showAddEventDialog(cellDate),
              onEventTap: (evt) => _confirmDelete(evt['id'].toString()),
            ),
          );
        }),
      ),
    );
  }

  Widget _buildMonthView() {
    const headers = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    return _glassPanel(
      child: Column(children: [
        // Fixed day-of-week header
        Row(
          children: headers
              .map((h) => Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      child: Text(h,
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: Colors.white54,
                              letterSpacing: 1)),
                    ),
                  ))
              .toList(),
        ),
        Container(height: 1, color: Colors.white.withValues(alpha: 0.05)),
        // Bidirectional infinite scroll via CustomScrollView + center key
        Expanded(
          child: LayoutBuilder(builder: (context, constraints) {
            _monthRowH = constraints.maxHeight / 5;
            final rowH = _monthRowH;
            return NotificationListener<ScrollNotification>(
              onNotification: _onMonthScroll,
              child: CustomScrollView(
                center: _monthCenterKey,
                controller: _monthScrollCtrl,
                physics: const ClampingScrollPhysics(),
                slivers: [
                  // ── Past weeks (rendered going upward from center) ──────
                  SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (ctx, i) => _buildWeekRow(-(i + 1), rowH),
                    ),
                  ),
                  // ── Anchor: current week + future weeks ───────────────
                  SliverList(
                    key: _monthCenterKey,
                    delegate: SliverChildBuilderDelegate(
                      (ctx, i) => _buildWeekRow(i, rowH),
                    ),
                  ),
                ],
              ),
            );
          }),
        ),
      ]),
    );
  }

  // ████████████████████████  WEEK VIEW  ████████████████████████████████████

  Widget _buildWeekView() {
    return PageView.builder(
      controller: _weekPageCtrl,
      physics: const PageScrollPhysics(parent: ClampingScrollPhysics()),
      scrollDirection: Axis.horizontal,
      onPageChanged: (idx) {
        if (_calcWeekIdx(_focusDate) == idx) return;
        final diff = idx - 10000;
        final base = _anchorDate.subtract(Duration(days: _anchorDate.weekday - 1));
        setState(() => _focusDate = base.add(Duration(days: diff * 7)));
        _fetchEventsDebounced();
      },
      itemBuilder: (ctx, idx) {
        final diff = idx - 10000;
        final base = _anchorDate.subtract(Duration(days: _anchorDate.weekday - 1));
        final pageStart = base.add(Duration(days: diff * 7));
        final weekDays = List.generate(7, (i) => pageStart.add(Duration(days: i)));
        final now = DateTime.now();

        return _buildTimeGridView(
          dayHeaders: weekDays.map((d) {
            final isToday = d.year == now.year && d.month == now.month && d.day == now.day;
            return _WeekDayHeader(date: d, isToday: isToday);
          }).toList(),
          eventLayer: _WeekEventLayer(
              days: weekDays,
              events: _events.values.toList(),
              onEventTap: (e) => _confirmDelete(e['id'].toString())),
          dayCount: 7,
          days: weekDays,
        );
      },
    );
  }

  // ████████████████████████  DAY VIEW  ████████████████████████████████████

  Widget _buildDayView() {
    return PageView.builder(
      controller: _dayPageCtrl,
      physics: const PageScrollPhysics(parent: ClampingScrollPhysics()),
      scrollDirection: Axis.horizontal,
      onPageChanged: (idx) {
        if (_calcDayIdx(_focusDate) == idx) return;
        final diff = idx - 10000;
        setState(() => _focusDate = _anchorDate.add(Duration(days: diff)));
        _fetchEventsDebounced();
      },
      itemBuilder: (ctx, idx) {
        final diff = idx - 10000;
        final pageDate = _anchorDate.add(Duration(days: diff));
        final now = DateTime.now();
        final isToday = pageDate.year == now.year && pageDate.month == now.month && pageDate.day == now.day;

        return _buildTimeGridView(
          dayHeaders: [_WeekDayHeader(date: pageDate, isToday: isToday)],
          eventLayer: _DayEventLayer(
              date: pageDate,
              events: _eventsForDate(pageDate),
              onEventTap: (e) => _confirmDelete(e['id'].toString())),
          dayCount: 1,
          days: [pageDate],
        );
      },
    );
  }

  // ── Shared time-grid scaffold ────────────────────────────────────────────
  Widget _buildTimeGridView({
    required List<Widget> dayHeaders,
    required Widget eventLayer,
    required int dayCount,
    required List<DateTime> days,
  }) {
    const hours = [
      '12 AM', '1 AM', '2 AM', '3 AM', '4 AM', '5 AM', '6 AM', '7 AM', '8 AM', '9 AM', '10 AM', '11 AM',
      '12 PM', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM', '6 PM', '7 PM', '8 PM', '9 PM', '10 PM', '11 PM',
    ];
    const hourH = 60.0;

    // All-day events: events that span entire days (date-only start string)
    final allDayEvents = _events.values
        .where((e) => _isAllDay(e) && days.any((d) => _eventSpansDay(e, d)))
        .toList();

    final now = DateTime.now();
    final hasToday = days.any((d) => d.year == now.year && d.month == now.month && d.day == now.day);


    return _glassPanel(
      child: Column(children: [
        // Day header row
        Row(children: [
          const SizedBox(width: 64),
          ...dayHeaders.map((h) => Expanded(child: h)),
        ]),
        Container(height: 1, color: Colors.white.withValues(alpha: 0.06)),
        // All-day events banner (only shown when there are all-day events)
        if (allDayEvents.isNotEmpty)
          _AllDayBanner(days: days, allDayEvents: allDayEvents),
        Expanded(
          child: SingleChildScrollView(
            controller: _timeGridScrollCtrl,
            child: SizedBox(
              height: hours.length * hourH,
              child: Row(children: [
                // Time column
                SizedBox(
                  width: 64,
                  child: Column(
                    children: hours
                        .map((h) => SizedBox(
                              height: hourH,
                              child: Align(
                                alignment: Alignment.topRight,
                                child: Padding(
                                  padding:
                                      const EdgeInsets.only(right: 12, top: 2),
                                  child: Text(h,
                                      style: const TextStyle(
                                          fontSize: 10,
                                          color: Colors.white30,
                                          fontWeight: FontWeight.w500)),
                                ),
                              ),
                            ))
                        .toList(),
                  ),
                ),
                // Grid + events
                Expanded(
                  child: Stack(children: [
                    // Horizontal lines
                    Column(
                      children: hours
                          .map((h) => Container(
                                height: hourH,
                                decoration: BoxDecoration(
                                  border: Border(
                                    bottom: BorderSide(
                                        color: Colors.white
                                            .withValues(alpha: 0.04)),
                                  ),
                                ),
                              ))
                          .toList(),
                    ),
                    // Events
                    eventLayer,
                    if (hasToday)
                      _CurrentTimeLine(
                        dayCount: dayCount,
                        startHour: 0,
                        hourH: hourH,
                      ),
                  ]),
                ),
              ]),
            ),
          ),
        ),
      ]),
    );
  }

  // Helper: does an all-day event touch a given calendar day?
  bool _eventSpansDay(dynamic e, DateTime d) {
    final startStr = e['start'] as String?;
    final endStr = e['end'] as String?;
    if (startStr == null) return false;
    try {
      final dateOnly = _isDateOnly(e);
      final startDate = dateOnly ? DateTime.parse(startStr) : DateTime.parse(startStr).toLocal();
      DateTime endDate = startDate;
      if (endStr != null) {
        endDate = dateOnly ? DateTime.parse(endStr) : DateTime.parse(endStr).toLocal();
        // Google Calendar end date for date-only events is exclusive
        if (dateOnly) {
          endDate = endDate.subtract(const Duration(days: 1));
        }
      }
      final target = DateTime(d.year, d.month, d.day);
      final startDay = DateTime(startDate.year, startDate.month, startDate.day);
      final endDay = DateTime(endDate.year, endDate.month, endDate.day);
      return !target.isBefore(startDay) && !target.isAfter(endDay);
    } catch (_) { return false; }
  }

  // ── Right sidebar ─────────────────────────────────────────────────────────
  Widget _buildRightSidebar() {
    return Container(
      width: 260,
      decoration: BoxDecoration(
        border: Border(
            left: BorderSide(color: Colors.white.withValues(alpha: 0.06))),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(children: [
        _MiniCalendar(
          focusDate: _focusDate,
          events: _events.values.toList(),
          onDayTap: (d) {
            setState(() => _focusDate = d);
            if (_view == CalView.month) {
              // if month changed, refetch
              if (d.month != _focusDate.month || d.year != _focusDate.year) {
                _fetchEvents(force: true);
              }
            }
          },
        ),
        const SizedBox(height: 20),
        Expanded(child: _buildAgendaPanel()),
      ]),
    );
  }

  Widget _buildAgendaPanel() {
    final dayEvts = _eventsForDate(_focusDate);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(children: [
          const Icon(Icons.view_agenda_outlined,
              size: 14, color: Colors.white38),
          const SizedBox(width: 6),
          Text(
              "Today's Agenda – ${DateFormat('MMM d').format(_focusDate)}",
              style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: Colors.white54,
                  letterSpacing: 0.5)),
        ]),
        const SizedBox(height: 12),
        Expanded(
          child: dayEvts.isEmpty
              ? Center(
                  child: Text('No events',
                      style: TextStyle(
                          fontSize: 13,
                          color: Colors.white.withValues(alpha: 0.25))))
              : ListView.separated(
                  itemCount: dayEvts.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (ctx, i) {
                    final e = dayEvts[i];
                    final color =
                        _eventColor(e['summary']?.toString());
                    final startStr = e['start'] as String? ?? '';
                    String timeStr = 'All Day';
                    try {
                      timeStr = DateFormat('h:mm a')
                          .format(DateTime.parse(startStr).toLocal());
                    } catch (_) {}
                    return GestureDetector(
                      onDoubleTap: () =>
                          _confirmDelete(e['id'].toString()),
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: color.withValues(alpha: 0.06),
                          borderRadius: BorderRadius.circular(4),
                          border: Border(
                              left:
                                  BorderSide(color: color, width: 2.5)),
                        ),
                        child: Column(
                            crossAxisAlignment:
                                CrossAxisAlignment.start,
                            children: [
                              Text(e['summary'] ?? 'Event',
                                  style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis),
                              const SizedBox(height: 4),
                              Text(timeStr,
                                  style: TextStyle(
                                      color: color,
                                      fontSize: 11,
                                      fontWeight: FontWeight.w500)),
                            ]),
                      ),
                    );
                  },
                ),
        ),
        const SizedBox(height: 12),
        InkWell(
          onTap: () => _showAddEventDialog(_focusDate),
          borderRadius: BorderRadius.circular(4),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.06),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(
                  color: Colors.white.withValues(alpha: 0.1)),
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.add, size: 14, color: Colors.white70),
                SizedBox(width: 6),
                Text('New Event',
                    style: TextStyle(
                        color: Colors.white70,
                        fontSize: 12,
                        fontWeight: FontWeight.w500)),
              ],
            ),
          ),
        ),
      ],
    );
  }

  // ── Glass container ───────────────────────────────────────────────────────
  Widget _glassPanel({required Widget child}) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(20),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.02),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
                color: Colors.white.withValues(alpha: 0.07), width: 1),
          ),
          child: child,
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// MONTH CELL
// ─────────────────────────────────────────────────────────────────────────────
class _MonthCell extends StatefulWidget {
  final DateTime cellDate;
  final String? monthName;
  final bool isToday, isSelected, isWeekend, isOutsideMonth;
  final List<dynamic> events;
  final VoidCallback onTap;
  final VoidCallback onAddTap;
  final void Function(dynamic evt) onEventTap;

  const _MonthCell({
    super.key,
    required this.cellDate,
    this.monthName,
    required this.isToday,
    required this.isSelected,
    required this.isWeekend,
    this.isOutsideMonth = false,
    required this.events,
    required this.onTap,
    required this.onAddTap,
    required this.onEventTap,
  });

  @override
  State<_MonthCell> createState() => _MonthCellState();
}

class _MonthCellState extends State<_MonthCell> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    Color bg = Colors.transparent;
    if (widget.isWeekend) bg = Colors.black.withValues(alpha: 0.1);
    if (widget.isSelected) bg = Colors.white.withValues(alpha: 0.05);
    if (_hovered) bg = Colors.white.withValues(alpha: 0.04);

    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
          onDoubleTap: widget.onAddTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          decoration: BoxDecoration(
            color: bg,
            border: Border(
              right:
                  BorderSide(color: Colors.white.withValues(alpha: 0.05)),
              bottom:
                  BorderSide(color: Colors.white.withValues(alpha: 0.05)),
            ),
            boxShadow: widget.isSelected
                ? [
                    BoxShadow(
                        color: Colors.white.withValues(alpha: 0.04),
                        blurRadius: 8)
                  ]
                : [],
          ),
          child: Stack(children: [
            if (widget.isSelected)
              Container(
                decoration: BoxDecoration(
                    border:
                        Border.all(color: Colors.white.withValues(alpha: 0.15),
                            width: 1)),
              ),
            Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Day number
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                    child: Row(children: [
                      const Spacer(),
                      widget.isToday
                          ? Container(
                              width: widget.monthName != null ? null : 26,
                              height: 26,
                              padding: widget.monthName != null ? const EdgeInsets.symmetric(horizontal: 8) : null,
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: widget.monthName != null ? BorderRadius.circular(13) : null,
                                shape: widget.monthName != null ? BoxShape.rectangle : BoxShape.circle,
                                boxShadow: [
                                  BoxShadow(
                                      color: Colors.white
                                          .withValues(alpha: 0.4),
                                      blurRadius: 12)
                                ],
                              ),
                              alignment: Alignment.center,
                              child: Text(widget.monthName != null ? '${widget.monthName} ${widget.cellDate.day}' : '${widget.cellDate.day}',
                                  style: const TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.black)),
                            )
                          : Text(widget.monthName != null ? '${widget.monthName} ${widget.cellDate.day}' : '${widget.cellDate.day}',
                              style: TextStyle(
                                  fontSize: 14,
                                  fontWeight: widget.monthName != null ? FontWeight.bold : FontWeight.w500,
                                  color: widget.isOutsideMonth 
                                      ? Colors.white.withValues(alpha: 0.15)
                                      : (widget.isWeekend
                                          ? Colors.white38
                                          : Colors.white60))),
                    ]),
                  ),
                  // Events (up to 2, then +N)
                  ...widget.events.take(2).map((e) {
                    final c = _eventColor(e['summary']?.toString());
                    final dateOnly = _isDateOnly(e);
                    final allDay = _isAllDay(e);
                    final birthday = _isBirthday(e);
                    
                    bool isFirstDay = true;
                    bool isLastDay = true;

                    if (!dateOnly) {
                      try {
                        final st = DateTime.parse(e['start'] as String).toLocal();
                        final et = e['end'] != null ? DateTime.parse(e['end'] as String).toLocal() : st;
                        isFirstDay = widget.cellDate.year == st.year && widget.cellDate.month == st.month && widget.cellDate.day == st.day;
                        isLastDay = widget.cellDate.year == et.year && widget.cellDate.month == et.month && widget.cellDate.day == et.day;
                      } catch (_) {}
                    } else {
                      try {
                        final st = DateTime.parse(e['start'] as String);
                        final et = e['end'] != null ? DateTime.parse(e['end'] as String).subtract(const Duration(days: 1)) : st;
                        isFirstDay = widget.cellDate.year == st.year && widget.cellDate.month == st.month && widget.cellDate.day == st.day;
                        isLastDay = widget.cellDate.year == et.year && widget.cellDate.month == et.month && widget.cellDate.day == et.day;
                      } catch (_) {}
                    }

                    final isSpanningLeft = allDay && !isFirstDay;
                    final isSpanningRight = allDay && !isLastDay;
                    final ml = isSpanningLeft ? 0.0 : 4.0;
                    final mr = isSpanningRight ? 0.0 : 4.0;

                    // For timed events (not dateOnly), we can show the time prefix.
                    String? timePrefix;
                    if (!dateOnly) {
                      if (!allDay || isFirstDay) {
                        try {
                          final dt = DateTime.parse(e['start'] as String).toLocal();
                          timePrefix = DateFormat('h:mm a').format(dt);
                        } catch (_) {}
                      }
                    }

                    return GestureDetector(
                      onTap: () => widget.onEventTap(e),
                      child: Container(
                        margin: EdgeInsets.only(bottom: 2, left: ml, right: mr),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 5, vertical: 2),
                      decoration: BoxDecoration(
                        color: allDay ? c : Colors.transparent,
                        borderRadius: BorderRadius.horizontal(
                          left: isSpanningLeft ? Radius.zero : const Radius.circular(4),
                          right: isSpanningRight ? Radius.zero : const Radius.circular(4),
                        ),
                      ),
                      child: Row(
                        children: [
                          if (birthday)
                            const Text('🎁 ', style: TextStyle(fontSize: 9)),
                          if (!allDay)
                            Container(
                               width: 6,
                               height: 6,
                               margin: const EdgeInsets.only(right: 4),
                               decoration: BoxDecoration(
                                 color: c,
                                 shape: BoxShape.circle,
                               ),
                            ),
                          if (timePrefix != null) ...[
                            Text(timePrefix,
                                style: const TextStyle(
                                    fontSize: 11,
                                    color: Colors.white,
                                    fontWeight: FontWeight.w600)),
                            const SizedBox(width: 4),
                          ],
                          Expanded(
                            child: Text(e['summary'] ?? 'Event',
                                style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.white,
                                    fontWeight: allDay ? FontWeight.bold : FontWeight.w600),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis),
                          ),
                        ],
                      ),
                    ));
                  }),
                  if (widget.events.length > 2)
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 8),
                      child: Text('+${widget.events.length - 2} more',
                          style: const TextStyle(
                              fontSize: 9, color: Colors.white38)),
                    ),
                ]),
            // Hover add button
            if (_hovered)
              Positioned(
                bottom: 4,
                right: 4,
                child: GestureDetector(
                  onTap: widget.onAddTap,
                  child: Icon(Icons.add_circle_outline,
                      size: 14,
                      color: Colors.white.withValues(alpha: 0.4)),
                ),
              ),
          ]),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// WEEK DAY HEADER
// ─────────────────────────────────────────────────────────────────────────────
class _WeekDayHeader extends StatelessWidget {
  final DateTime date;
  final bool isToday;

  const _WeekDayHeader({required this.date, required this.isToday});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: isToday
          ? BoxDecoration(
              border: const Border(
                  top: BorderSide(color: Colors.white, width: 2)))
          : null,
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Text(DateFormat('EEE').format(date).toUpperCase(),
            style: TextStyle(
                fontSize: 11,
                letterSpacing: 1.2,
                fontWeight: FontWeight.w600,
                color:
                    isToday ? Colors.white : Colors.white38)),
        const SizedBox(height: 4),
        Text(DateFormat('d').format(date),
            style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w600,
                color:
                    isToday ? Colors.white : Colors.white60)),
      ]),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// ALL DAY BANNER
// ─────────────────────────────────────────────────────────────────────────────
class _AllDayBanner extends StatelessWidget {
  final List<DateTime> days;
  final List<dynamic> allDayEvents;

  const _AllDayBanner({required this.days, required this.allDayEvents});

  bool _spansDay(dynamic e, DateTime d) {
    final startStr = e['start'] as String?;
    final endStr = e['end'] as String?;
    if (startStr == null) return false;
    try {
      final dateOnly = _isDateOnly(e);
      final startDate = dateOnly ? DateTime.parse(startStr) : DateTime.parse(startStr).toLocal();
      DateTime endDate = startDate;
      if (endStr != null) {
        endDate = dateOnly ? DateTime.parse(endStr) : DateTime.parse(endStr).toLocal();
        if (dateOnly) endDate = endDate.subtract(const Duration(days: 1));
      }
      final target = DateTime(d.year, d.month, d.day);
      final startDay = DateTime(startDate.year, startDate.month, startDate.day);
      final endDay = DateTime(endDate.year, endDate.month, endDate.day);
      return !target.isBefore(startDay) && !target.isAfter(endDay);
    } catch (_) { return false; }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.02),
        border: Border(bottom: BorderSide(color: Colors.white.withValues(alpha: 0.06))),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // "All-day" label column (matches the 64px time column width)
          SizedBox(
            width: 64,
            child: Padding(
              padding: const EdgeInsets.only(right: 8, top: 4, bottom: 4),
              child: Text('All-day',
                  textAlign: TextAlign.right,
                  style: TextStyle(fontSize: 9, color: Colors.white.withValues(alpha: 0.3))),
            ),
          ),
          // One column per day
          ...days.map((d) {
            final dayEvents = allDayEvents.where((e) => _spansDay(e, d)).toList();
            return Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: dayEvents.map((e) {
                  final color = _eventColor(e['summary']?.toString());
                  final birthday = _isBirthday(e);
                  final dateOnly = _isDateOnly(e);
                  
                  final startStr = e['start'] as String?;
                  final endStr = e['end'] as String?;
                  DateTime? startDate, endDate;
                  try {
                    if (startStr != null) startDate = dateOnly ? DateTime.parse(startStr) : DateTime.parse(startStr).toLocal();
                    if (endStr != null) {
                      endDate = dateOnly ? DateTime.parse(endStr) : DateTime.parse(endStr).toLocal();
                      if (dateOnly) endDate = endDate.subtract(const Duration(days: 1));
                    }
                  } catch (_) {}
                  
                  final isStart = startDate != null && DateUtils.isSameDay(d, startDate);
                  final isEnd = (endDate != null) ? DateUtils.isSameDay(d, endDate) : isStart;
                  
                  final ml = isStart ? 1.0 : 0.0;
                  final mr = isEnd ? 1.0 : 0.0;

                  String? timePrefix;
                  if (isStart && !dateOnly && startStr != null) {
                    try {
                      final dt = DateTime.parse(startStr).toLocal();
                      timePrefix = DateFormat('h:mm a').format(dt);
                    } catch (_) {}
                  }

                  return Container(
                    margin: EdgeInsets.only(top: 1, bottom: 1, left: ml, right: mr),
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                    decoration: BoxDecoration(
                      color: color,
                      borderRadius: BorderRadius.horizontal(
                        left: isStart ? const Radius.circular(4) : Radius.zero,
                        right: isEnd ? const Radius.circular(4) : Radius.zero,
                      ),
                    ),
                    child: Row(children: [
                      if (birthday) const Text('🎁 ', style: TextStyle(fontSize: 9)),
                      if (timePrefix != null) ...[
                        Text(timePrefix, style: const TextStyle(fontSize: 10, color: Colors.white, fontWeight: FontWeight.w600)),
                        const SizedBox(width: 4),
                      ],
                      Expanded(
                        child: Text(isStart ? (e['summary'] ?? '') : '',
                            style: const TextStyle(fontSize: 10, color: Colors.white, fontWeight: FontWeight.w500),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis),
                      ),
                    ]),
                  );
                }).toList(),
              ),
            );
          }),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// WEEK EVENT LAYER
// ─────────────────────────────────────────────────────────────────────────────
class _WeekEventLayer extends StatelessWidget {
  final List<DateTime> days;
  final List<dynamic> events;
  final void Function(dynamic) onEventTap;

  const _WeekEventLayer({
    required this.days,
    required this.events,
    required this.onEventTap,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (ctx, constraints) {
      final colW = constraints.maxWidth / days.length;
      const hourH = 60.0;
      const startHour = 0;

      return Stack(children: [
        // Vertical column separators
        ...List.generate(days.length - 1, (i) => Positioned(
              left: colW * (i + 1),
              top: 0,
              bottom: 0,
              child: Container(
                  width: 1,
                  color: Colors.white.withValues(alpha: 0.04)),
            )),

        // Events (skip all-day; they go in the banner above the grid)
        ...events.where((e) => !_isAllDay(e)).expand((e) {
          final startStr = e['start'] as String?;
          final endStr = e['end'] as String?;
          if (startStr == null) return <Widget>[];

          DateTime startDt, endDt;
          try {
            startDt = DateTime.parse(startStr).toLocal();
            endDt = endStr != null
                ? DateTime.parse(endStr).toLocal()
                : startDt.add(const Duration(hours: 1));
          } catch (_) {
            return <Widget>[];
          }

          final widgets = <Widget>[];

          for (int colIdx = 0; colIdx < days.length; colIdx++) {
            final d = days[colIdx];
            final colStart = DateTime(d.year, d.month, d.day);
            final colEnd = DateTime(d.year, d.month, d.day, 23, 59, 59);

            if (startDt.isAfter(colEnd) || endDt.isBefore(colStart) || endDt.isAtSameMomentAs(colStart)) {
              continue;
            }

            final drawStart = startDt.isBefore(colStart) ? colStart : startDt;
            final drawEnd = endDt.isAfter(colEnd) ? colEnd : endDt;

            final startMin = (drawStart.hour - startHour) * 60 + drawStart.minute;
            final durMin = drawEnd.difference(drawStart).inMinutes;
            final top = startMin / 60 * hourH;
            final height = (durMin / 60 * hourH).clamp(20.0, double.infinity);

            final color = _eventColor(e['summary']?.toString());

            widgets.add(
              Positioned(
                left: colW * colIdx + 2,
                top: top,
                width: colW - 4,
                height: height,
                child: GestureDetector(
                  onDoubleTap: () => onEventTap(e),
                  child: Container(
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(6),
                      border: Border(
                          left: BorderSide(color: color, width: 3)),
                    ),
                    padding: const EdgeInsets.symmetric(
                        horizontal: 6, vertical: 4),
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(e['summary'] ?? 'Event',
                              style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: color),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis),
                          Text(
                              '${DateFormat('h:mm a').format(drawStart)} – ${DateFormat('h:mm a').format(drawEnd)}',
                              style: const TextStyle(
                                  fontSize: 9,
                                  color: Colors.white54),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis),
                        ]),
                  ),
                ),
              ),
            );
          }
          return widgets;
        }),
      ]);
    });
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// DAY EVENT LAYER
// ─────────────────────────────────────────────────────────────────────────────
class _DayEventLayer extends StatelessWidget {
  final DateTime date;
  final List<dynamic> events;
  final void Function(dynamic) onEventTap;

  const _DayEventLayer({
    required this.date,
    required this.events,
    required this.onEventTap,
  });

  @override
  Widget build(BuildContext context) {
    const hourH = 60.0;
    const startHour = 0;

    return LayoutBuilder(builder: (ctx, constraints) {
      return Stack(children: [
        // All-day events go to the banner; skip them here
        ...events.where((e) => !_isAllDay(e)).expand((e) {
          final startStr = e['start'] as String?;
          final endStr = e['end'] as String?;
          if (startStr == null) return <Widget>[];

          DateTime startDt, endDt;
          try {
            startDt = DateTime.parse(startStr).toLocal();
            endDt = endStr != null
                ? DateTime.parse(endStr).toLocal()
                : startDt.add(const Duration(hours: 1));
          } catch (_) {
            return <Widget>[];
          }

          final widgets = <Widget>[];

          final colStart = DateTime(date.year, date.month, date.day);
          final colEnd = DateTime(date.year, date.month, date.day, 23, 59, 59);

          if (startDt.isAfter(colEnd) || endDt.isBefore(colStart) || endDt.isAtSameMomentAs(colStart)) {
            return <Widget>[];
          }

          final drawStart = startDt.isBefore(colStart) ? colStart : startDt;
          final drawEnd = endDt.isAfter(colEnd) ? colEnd : endDt;

          final startMin = (drawStart.hour - startHour) * 60 + drawStart.minute;
          final durMin = drawEnd.difference(drawStart).inMinutes;
          final top = startMin / 60 * hourH;
          final height = (durMin / 60 * hourH).clamp(24.0, double.infinity);
          final color = _eventColor(e['summary']?.toString());

          widgets.add(
            Positioned(
              left: 12,
              right: 12,
              top: top,
              height: height,
              child: GestureDetector(
                onDoubleTap: () => onEventTap(e),
                child: Container(
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border(
                        left: BorderSide(color: color, width: 3)),
                    boxShadow: [
                      BoxShadow(
                          color: color.withValues(alpha: 0.15),
                          blurRadius: 12)
                    ],
                  ),
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 8),
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(e['summary'] ?? 'Event',
                            style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                                color: color)),
                        if (height > 36)
                          Text(
                              '${DateFormat('h:mm a').format(drawStart)} – ${DateFormat('h:mm a').format(drawEnd)}',
                              style: const TextStyle(
                                  fontSize: 11,
                                  color: Colors.white54)),
                        if (height > 60 &&
                            (e['location'] ?? '').isNotEmpty)
                          Text('📍 ${e['location']}',
                              style: const TextStyle(
                                  fontSize: 10,
                                  color: Colors.white38)),
                      ]),
                ),
              ),
            ),
          );
          
          return widgets;
        }),
      ]);
    });
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// CURRENT TIME LINE
// ─────────────────────────────────────────────────────────────────────────────
class _CurrentTimeLine extends StatefulWidget {
  final int dayCount, startHour;
  final double hourH;

  const _CurrentTimeLine(
      {required this.dayCount,
      required this.startHour,
      required this.hourH});

  @override
  State<_CurrentTimeLine> createState() => _CurrentTimeLineState();
}

class _CurrentTimeLineState extends State<_CurrentTimeLine> {
  late Timer _timer;

  @override
  void initState() {
    super.initState();
    // Update the line position every minute
    _timer = Timer.periodic(const Duration(minutes: 1), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _timer.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();
    final minFromStart = (now.hour - widget.startHour) * 60 + now.minute;
    final top = minFromStart / 60 * widget.hourH;
    
    if (top < 0) return const SizedBox();
    
    return AnimatedPositioned(
      duration: const Duration(seconds: 1),
      curve: Curves.easeInOut,
      top: top - 10, // Shift up slightly to vertically center the pill on the time
      left: 0,
      right: 0,
      child: Row(children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: Colors.redAccent,
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(DateFormat('h:mm a').format(now), style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w600)),
        ),
        Expanded(
            child: Container(
                height: 1.5, 
                decoration: BoxDecoration(
                  color: Colors.redAccent.withValues(alpha: 0.8),
                  boxShadow: [
                    BoxShadow(
                        color: Colors.redAccent.withValues(alpha: 0.5), 
                        blurRadius: 4, 
                        spreadRadius: 1)
                  ]
                ))),
      ]),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// MINI CALENDAR (sidebar)
// ─────────────────────────────────────────────────────────────────────────────
class _MiniCalendar extends StatelessWidget {
  final DateTime focusDate;
  final List<dynamic> events;
  final void Function(DateTime) onDayTap;

  const _MiniCalendar({
    required this.focusDate,
    required this.events,
    required this.onDayTap,
  });

  bool _hasEvents(DateTime date) => events.any((e) {
        final start = e['start'] as String?;
        if (start == null) return false;
        try {
          final dt = DateTime.parse(start).toLocal();
          return dt.year == date.year &&
              dt.month == date.month &&
              dt.day == date.day;
        } catch (_) {
          return false;
        }
      });

  @override
  Widget build(BuildContext context) {
    final first = DateTime(focusDate.year, focusDate.month, 1);
    final daysInMonth =
        DateUtils.getDaysInMonth(focusDate.year, focusDate.month);
    final startOffset = first.weekday % 7;
    final now = DateTime.now();

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(DateFormat('MMMM yyyy').format(focusDate),
          style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: Colors.white70)),
      const SizedBox(height: 12),
      // Weekday labels
      Row(
        children: ['S', 'M', 'T', 'W', 'T', 'F', 'S']
            .map((d) => Expanded(
                  child: Center(
                    child: Text(d,
                        style: const TextStyle(
                            fontSize: 9,
                            color: Colors.white30,
                            fontWeight: FontWeight.w600)),
                  ),
                ))
            .toList(),
      ),
      const SizedBox(height: 6),
      GridView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 7, mainAxisExtent: 28),
        itemCount: 42,
        itemBuilder: (ctx, i) {
          final dayNum = i - startOffset + 1;
          if (dayNum < 1 || dayNum > daysInMonth) return const SizedBox();
          final date =
              DateTime(focusDate.year, focusDate.month, dayNum);
          final isToday = date.year == now.year &&
              date.month == now.month &&
              date.day == now.day;
          final isSelected = date.year == focusDate.year &&
              date.month == focusDate.month &&
              date.day == focusDate.day;
          final hasEvt = _hasEvents(date);

          return GestureDetector(
            onTap: () => onDayTap(date),
            child: Center(
              child: Container(
                width: 26,
                height: 26,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: isSelected
                      ? Colors.white.withValues(alpha: 0.15)
                      : isToday
                          ? Colors.white
                          : Colors.transparent,
                ),
                child: Stack(alignment: Alignment.center, children: [
                  Text('$dayNum',
                      style: TextStyle(
                          fontSize: 11,
                          fontWeight: isSelected || isToday
                              ? FontWeight.bold
                              : FontWeight.normal,
                          color: isToday && !isSelected
                              ? Colors.black
                              : Colors.white70)),
                  if (hasEvt && !isToday)
                    Positioned(
                      bottom: 2,
                      child: Container(
                          width: 3,
                          height: 3,
                          decoration: const BoxDecoration(
                              color: Colors.white54,
                              shape: BoxShape.circle)),
                    ),
                ]),
              ),
            ),
          );
        },
      ),
    ]);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// ANIMATIONS & INTERACTIVE COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

class _BouncyButton extends StatefulWidget {
  final Widget child;
  final VoidCallback onTap;
  const _BouncyButton({required this.child, required this.onTap});

  @override
  State<_BouncyButton> createState() => _BouncyButtonState();
}

class _BouncyButtonState extends State<_BouncyButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 150));
    _scale = Tween<double>(begin: 1.0, end: 0.92).animate(
        CurvedAnimation(parent: _ctrl, curve: Curves.easeInOutCubic));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _ctrl.forward(),
      onTapUp: (_) {
        _ctrl.reverse();
        widget.onTap();
      },
      onTapCancel: () => _ctrl.reverse(),
      child: ScaleTransition(
        scale: _scale,
        child: widget.child,
      ),
    );
  }
}

class _SegmentedToggle extends StatelessWidget {
  final CalView currentView;
  final ValueChanged<CalView> onChanged;

  const _SegmentedToggle({required this.currentView, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    // 0 -> Day, 1 -> Week, 2 -> Month
    final idx = CalView.values.indexOf(currentView);
    return Container(
      width: 190, // Fixed width to accommodate all 3 items properly
      height: 32,
      padding: const EdgeInsets.all(2),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
      ),
      child: Stack(
        children: [
          // Sliding indicator pill
          AnimatedAlign(
            duration: const Duration(seconds: 10),
            curve: Curves.easeOutCubic,
            alignment: idx == 0 
                ? Alignment.centerLeft 
                : idx == 1 
                    ? Alignment.center 
                    : Alignment.centerRight,
            child: FractionallySizedBox(
              widthFactor: 1 / 3,
              heightFactor: 1,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(999),
                  boxShadow: [
                    BoxShadow(color: Colors.black.withValues(alpha: 0.2), blurRadius: 4)
                  ]
                ),
              ),
            ),
          ),
          // Buttons
          Row(
            children: CalView.values.map((v) {
              final active = v == currentView;
              return Expanded(
                child: GestureDetector(
                  onTap: () => onChanged(v),
                  behavior: HitTestBehavior.opaque,
                  child: Center(
                    child: AnimatedDefaultTextStyle(
                      duration: const Duration(milliseconds: 200),
                      style: TextStyle(
                        fontFamily: 'Geist',
                        fontSize: 12,
                        fontWeight: active ? FontWeight.w600 : FontWeight.w500,
                        color: active ? Colors.white : Colors.white54,
                      ),
                      child: Text(v.name[0].toUpperCase() + v.name.substring(1)),
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}


class _RichAddEventDialog extends StatefulWidget {
  final DateTime initialDate;
  final TimeOfDay initialTime;
  final Function(String title, String desc, DateTime start, DateTime end, bool allDay) onSave;

  const _RichAddEventDialog({
    super.key,
    required this.initialDate,
    required this.initialTime,
    required this.onSave,
  });

  @override
  State<_RichAddEventDialog> createState() => _RichAddEventDialogState();
}

class _RichAddEventDialogState extends State<_RichAddEventDialog> {
  final TextEditingController _titleCtrl = TextEditingController();
  final TextEditingController _descCtrl = TextEditingController();

  late DateTime _startDate;
  late TimeOfDay _startTime;
  late DateTime _endDate;
  late TimeOfDay _endTime;
  bool _isAllDay = false;
  int _tabIndex = 0;

  @override
  void initState() {
    super.initState();
    _startDate = widget.initialDate;
    _startTime = widget.initialTime;
    _endDate = widget.initialDate;
    final startDt = DateTime(2000, 1, 1, _startTime.hour, _startTime.minute);
    final endDt = startDt.add(const Duration(hours: 1));
    _endTime = TimeOfDay(hour: endDt.hour, minute: endDt.minute);
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickDate(bool isStart) async {
    final d = await showDatePicker(
      context: context,
      initialDate: isStart ? _startDate : _endDate,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (d != null) {
      setState(() {
        if (isStart) {
          _startDate = d;
          if (_endDate.isBefore(_startDate)) _endDate = _startDate;
        } else {
          _endDate = d;
          if (_startDate.isAfter(_endDate)) _startDate = _endDate;
        }
      });
    }
  }

  Future<void> _pickTime(bool isStart) async {
    final t = await showTimePicker(
      context: context,
      initialTime: isStart ? _startTime : _endTime,
    );
    if (t != null) {
      setState(() {
        if (isStart) _startTime = t;
        else _endTime = t;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      insetPadding: const EdgeInsets.all(20),
      child: Container(
        width: 500,
        decoration: BoxDecoration(
          color: const Color(0xFF161618),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white.withOpacity(0.08), width: 1.5),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.5),
              blurRadius: 32,
              offset: const Offset(0, 16),
            )
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFF232326),
                  border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.05))),
                ),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.close, color: Colors.white70, size: 20),
                      onPressed: () => Navigator.pop(context),
                      hoverColor: Colors.white.withOpacity(0.1),
                      splashRadius: 20,
                    ),
                    const SizedBox(width: 8),
                    const Text('Add event', style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500)),
                    const Spacer(),
                    MouseRegion(
                      cursor: SystemMouseCursors.click,
                      child: GestureDetector(
                        onTap: () {
                          if (_titleCtrl.text.isEmpty) _titleCtrl.text = 'Untitled Event';
                          final start = DateTime(_startDate.year, _startDate.month, _startDate.day, _isAllDay ? 0 : _startTime.hour, _isAllDay ? 0 : _startTime.minute);
                          final end = DateTime(_endDate.year, _endDate.month, _endDate.day, _isAllDay ? 0 : _endTime.hour, _isAllDay ? 0 : _endTime.minute);
                          widget.onSave(_titleCtrl.text, _descCtrl.text, start, end, _isAllDay);
                        },
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(colors: [Color(0xFF3B82F6), Color(0xFF2563EB)]),
                            borderRadius: BorderRadius.circular(20),
                            boxShadow: [
                              BoxShadow(color: const Color(0xFF3B82F6).withOpacity(0.3), blurRadius: 8, offset: const Offset(0, 2))
                            ]
                          ),
                          child: const Text('Save', style: TextStyle(fontWeight: FontWeight.w600, color: Colors.white, fontSize: 13)),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                  ],
                ),
              ),

              Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    TextField(
                      controller: _titleCtrl,
                      style: const TextStyle(fontSize: 24, color: Colors.white, fontWeight: FontWeight.w400),
                      decoration: InputDecoration(
                        hintText: 'Add title and time',
                        hintStyle: TextStyle(fontSize: 24, color: Colors.white.withOpacity(0.3)),
                        enabledBorder: UnderlineInputBorder(borderSide: BorderSide(color: Colors.white.withOpacity(0.2))),
                        focusedBorder: const UnderlineInputBorder(borderSide: BorderSide(color: Color(0xFF3B82F6), width: 2)),
                        isDense: true,
                        contentPadding: const EdgeInsets.only(bottom: 8),
                      ),
                    ),
                    const SizedBox(height: 20),

                    Row(
                      children: [
                        _buildTab(0, 'Event'),
                        const SizedBox(width: 8),
                        _buildTab(1, 'Task'),
                      ],
                    ),
                    const SizedBox(height: 24),

                    Row(
                      children: [
                        const Icon(Icons.access_time, color: Colors.white54, size: 20),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Wrap(
                                crossAxisAlignment: WrapCrossAlignment.center,
                                spacing: 4,
                                runSpacing: 8,
                                children: [
                                  _buildHoverBtn(DateFormat('EEEE, d MMMM').format(_startDate), () => _pickDate(true)),
                                  if (!_isAllDay) _buildHoverBtn(_startTime.format(context), () => _pickTime(true)),
                                  const Padding(padding: EdgeInsets.symmetric(horizontal: 4), child: Text('–', style: TextStyle(color: Colors.white54))),
                                  if (!_isAllDay) _buildHoverBtn(_endTime.format(context), () => _pickTime(false)),
                                  _buildHoverBtn(DateFormat('EEEE, d MMMM').format(_endDate), () => _pickDate(false)),
                                ],
                              ),
                              const SizedBox(height: 12),
                              Row(
                                children: [
                                  SizedBox(
                                    width: 24,
                                    height: 24,
                                    child: Checkbox(
                                      value: _isAllDay,
                                      activeColor: const Color(0xFF3B82F6),
                                      checkColor: Colors.white,
                                      side: BorderSide(color: Colors.white.withOpacity(0.4)),
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                                      onChanged: (v) => setState(() => _isAllDay = v ?? false),
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  const Text('All day', style: TextStyle(color: Colors.white70, fontSize: 13)),
                                  const SizedBox(width: 24),
                                  _buildHoverBtn('Does not repeat ▾', () {}),
                                ],
                              )
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 24),

                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Padding(padding: EdgeInsets.only(top: 10), child: Icon(Icons.sort, color: Colors.white54, size: 20)),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Container(
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.04),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Colors.white.withOpacity(0.1)),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                  decoration: BoxDecoration(
                                    border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.05))),
                                  ),
                                  child: Row(
                                    children: [
                                      _iconBtn(Icons.format_bold),
                                      _iconBtn(Icons.format_italic),
                                      _iconBtn(Icons.format_underlined),
                                      const SizedBox(width: 12),
                                      _iconBtn(Icons.format_list_bulleted),
                                      _iconBtn(Icons.format_list_numbered),
                                      const SizedBox(width: 12),
                                      _iconBtn(Icons.link),
                                    ],
                                  ),
                                ),
                                Padding(
                                  padding: const EdgeInsets.all(12),
                                  child: TextField(
                                    controller: _descCtrl,
                                    style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.5),
                                    maxLines: 4,
                                    decoration: const InputDecoration(
                                      hintText: 'Add description',
                                      hintStyle: TextStyle(color: Colors.white38, fontSize: 13),
                                      border: InputBorder.none,
                                      isDense: true,
                                      contentPadding: EdgeInsets.zero,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    )
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTab(int index, String label) {
    final active = _tabIndex == index;
    return GestureDetector(
      onTap: () => setState(() => _tabIndex = index),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: active ? const Color(0xFF3B82F6).withOpacity(0.2) : Colors.transparent,
          borderRadius: BorderRadius.circular(6),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: active ? const Color(0xFF3B82F6) : Colors.white60,
            fontWeight: active ? FontWeight.w600 : FontWeight.w500,
            fontSize: 13,
          ),
        ),
      ),
    );
  }

  Widget _iconBtn(IconData icon) {
    return InkWell(
      onTap: () {},
      borderRadius: BorderRadius.circular(4),
      child: Padding(
        padding: const EdgeInsets.all(4.0),
        child: Icon(icon, color: Colors.white54, size: 18),
      ),
    );
  }

  Widget _buildHoverBtn(String text, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(6),
      hoverColor: Colors.white.withOpacity(0.08),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        child: Text(text, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500)),
      ),
    );
  }
}
