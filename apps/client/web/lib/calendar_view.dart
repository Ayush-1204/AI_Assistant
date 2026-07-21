import 'dart:async';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'providers/auth_provider.dart';

// ─── Event color palette (cycles by hash) ─────────────────────────────────
const _kEventColors = [
  Color(0xFF2979FF), // blue  – Team Sync
  Color(0xFFFFB300), // amber – Deadlines
  Color(0xFFB39DDB), // lavender – Personal
  Color(0xFF4CAF50), // green
  Color(0xFFFF5722), // deep orange
];

Color _eventColor(String? summary) {
  if (summary == null || summary.isEmpty) return _kEventColors[0];
  return _kEventColors[(summary.hashCode.abs()) % _kEventColors.length];
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
  List<dynamic> _events = [];
  bool _isLoading = true;
  int _slideDir = 1;

  late AnimationController _fadeCtrl;
  ScrollController? _timeGridScrollCtrl;
  
  Timer? _debounceTimer;

  late PageController _monthPageCtrl;
  late PageController _weekPageCtrl;
  late PageController _dayPageCtrl;
  
  final DateTime _anchorDate = DateTime.now();

  int _calcMonthIdx(DateTime d) => 10000 + ((d.year - _anchorDate.year) * 12 + (d.month - _anchorDate.month));
  int _calcWeekIdx(DateTime d) {
    final startNow = _anchorDate.subtract(Duration(days: _anchorDate.weekday - 1));
    final startTarget = d.subtract(Duration(days: d.weekday - 1));
    return 10000 + (startTarget.difference(startNow).inDays / 7).round();
  }
  int _calcDayIdx(DateTime d) => 10000 + d.difference(_anchorDate).inDays;


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
        
    _monthPageCtrl = PageController(initialPage: _calcMonthIdx(_focusDate));
    _weekPageCtrl = PageController(initialPage: _calcWeekIdx(_focusDate));
    _dayPageCtrl = PageController(initialPage: _calcDayIdx(_focusDate));
        
    _fetchEvents();
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _fadeCtrl.dispose();
    _timeGridScrollCtrl?.dispose();
    _monthPageCtrl.dispose();
    _weekPageCtrl.dispose();
    _dayPageCtrl.dispose();
    super.dispose();
  }

  // ── Data fetching ────────────────────────────────────────────────────────
  void _fetchEventsDebounced() {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 250), () {
      if (mounted) _fetchEvents();
    });
  }

  Future<void> _fetchEvents() async {
    // Never show loading spinner once events are already shown
    // Only show spinner on very first load
    final bool firstLoad = _events.isEmpty;
    if (firstLoad && mounted) {
      setState(() => _isLoading = true);
      _fadeCtrl.reset();
    }

    try {
      final api = ref.read(apiClientProvider);
      final evts = await api.fetchCalendarEvents(
          year: _focusDate.year, month: _focusDate.month);

      if (mounted) {
        setState(() {
          _events = evts;
          _isLoading = false;
        });
        if (firstLoad) _fadeCtrl.forward();
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
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
        _monthPageCtrl.nextPage(
            duration: const Duration(milliseconds: 220), curve: Curves.easeOut);
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
        _monthPageCtrl.previousPage(
            duration: const Duration(milliseconds: 220), curve: Curves.easeOut);
        break;
    }
  }

  void _goToday() {
    _jumpToDate(DateTime.now());
  }

  void _jumpToDate(DateTime d) {
    setState(() => _focusDate = d);
    if (_monthPageCtrl.hasClients) {
      _monthPageCtrl.animateToPage(_calcMonthIdx(d),
          duration: const Duration(milliseconds: 120), curve: Curves.easeOut);
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
    return _events.where((e) {
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
    }).toList();
  }

  // ── Add event dialog ─────────────────────────────────────────────────────
  Future<void> _showAddEventDialog([DateTime? preselected]) async {
    final titleCtrl = TextEditingController();
    final descCtrl = TextEditingController();
    DateTime selDate = preselected ?? _focusDate;
    TimeOfDay selTime = const TimeOfDay(hour: 10, minute: 0);

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(builder: (context, setSB) {
        return AlertDialog(
          backgroundColor: const Color(0xFF131313),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
            side: BorderSide(color: Colors.white.withValues(alpha: 0.1)),
          ),
          title: const Text('New Event',
              style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 20)),
          content: SizedBox(
            width: 380,
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              _dialogField(titleCtrl, 'Event Title'),
              const SizedBox(height: 12),
              _dialogField(descCtrl, 'Description'),
              const SizedBox(height: 20),
              Row(children: [
                Expanded(
                    child: _dateTile(ctx, selDate, () async {
                  final d = await showDatePicker(
                      context: ctx,
                      initialDate: selDate,
                      firstDate: DateTime(2000),
                      lastDate: DateTime(2100));
                  if (d != null) setSB(() => selDate = d);
                })),
                const SizedBox(width: 12),
                Expanded(
                    child: _timeTile(ctx, selTime, () async {
                  final t =
                      await showTimePicker(context: ctx, initialTime: selTime);
                  if (t != null) setSB(() => selTime = t);
                })),
              ])
            ]),
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Cancel',
                    style: TextStyle(color: Colors.white54))),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: Colors.black,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12))),
              onPressed: () async {
                if (titleCtrl.text.isEmpty) return;
                final start = DateTime(selDate.year, selDate.month, selDate.day,
                    selTime.hour, selTime.minute);
                final end = start.add(const Duration(hours: 1));
                Navigator.pop(ctx);
                setState(() => _isLoading = true);
                try {
                  await ref.read(apiClientProvider).createCalendarEvent(
                      titleCtrl.text,
                      descCtrl.text,
                      start.toUtc().toIso8601String(),
                      end.toUtc().toIso8601String());
                } catch (_) {}
                _fetchEvents();
              },
              child: const Text('Save Event'),
            ),
          ],
        );
      }),
    );
  }

  Widget _dialogField(TextEditingController ctrl, String label) =>
      TextField(
        controller: ctrl,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: Colors.white54),
          enabledBorder: UnderlineInputBorder(
              borderSide:
                  BorderSide(color: Colors.white.withValues(alpha: 0.15))),
          focusedBorder: const UnderlineInputBorder(
              borderSide: BorderSide(color: Colors.white38)),
        ),
      );

  Widget _dateTile(BuildContext ctx, DateTime d, VoidCallback onTap) =>
      InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: _tileBox(
            'Date', DateFormat('MMM dd, yyyy').format(d)),
      );

  Widget _timeTile(BuildContext ctx, TimeOfDay t, VoidCallback onTap) =>
      InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: _tileBox('Time', t.format(ctx)),
      );

  Widget _tileBox(String label, String val) => Container(
        padding:
            const EdgeInsets.symmetric(vertical: 12, horizontal: 14),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.04),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label,
              style: const TextStyle(fontSize: 10, color: Colors.white38)),
          const SizedBox(height: 4),
          Text(val,
              style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: Colors.white)),
        ]),
      );

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
      _fetchEvents();
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
          child: _isLoading && _events.isEmpty
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
        const SizedBox(width: 16),
        _navBtn(Icons.chevron_left, _goPrev),
        const SizedBox(width: 4),
        _navBtn(Icons.chevron_right, _goNext),
        const SizedBox(width: 12),
        _todayBtn(),
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
        if (_view != v) setState(() => _view = v);
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
            borderRadius: BorderRadius.circular(10),
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

  Widget _buildMonthView() {
    const headers = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    return _glassPanel(
      child: Column(children: [
        // Header row
        Row(
          children: headers
              .map((h) => Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 10),
                      child: Text(h,
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: Colors.white38,
                              letterSpacing: 1)),
                    ),
                  ))
              .toList(),
        ),
        Container(height: 1, color: Colors.white.withValues(alpha: 0.05)),
        Expanded(
          child: PageView.builder(
            controller: _monthPageCtrl,
            physics: const PageScrollPhysics(parent: ClampingScrollPhysics()),
            scrollDirection: Axis.vertical,
            onPageChanged: (idx) {
              final diff = idx - 10000;
              final newDate = DateTime(_anchorDate.year, _anchorDate.month + diff, 1);
              setState(() => _focusDate = newDate);
              _fetchEventsDebounced();
            },
            itemBuilder: (ctx, idx) {
              final diff = idx - 10000;
              final pageDate = DateTime(_anchorDate.year, _anchorDate.month + diff, 1);
              final first = DateTime(pageDate.year, pageDate.month, 1);
              final daysInMonth = DateUtils.getDaysInMonth(pageDate.year, pageDate.month);
              final startOffset = first.weekday % 7; // Sun=0

              return GridView.builder(
                padding: EdgeInsets.zero,
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate:
                    const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 7,
                        mainAxisExtent: 110),
                itemCount: 42,
                itemBuilder: (ctx, i) {
                  final dayNum = i - startOffset + 1;
                  if (dayNum < 1 || dayNum > daysInMonth) {
                    final int prevDays = pageDate.month == 1 
                        ? DateUtils.getDaysInMonth(pageDate.year - 1, 12)
                        : DateUtils.getDaysInMonth(pageDate.year, pageDate.month - 1);
                    
                    final emptyDay = dayNum < 1 ? prevDays + dayNum : dayNum - daysInMonth;
                    return _emptyMonthCell(emptyDay, i % 7);
                  }
                  final date = DateTime(pageDate.year, pageDate.month, dayNum);
                  final today = DateTime.now();
                  final isToday = date.year == today.year && date.month == today.month && date.day == today.day;
                  final isSelected = date.year == _focusDate.year && date.month == _focusDate.month && date.day == _focusDate.day;
                  final dayEvts = _eventsForDate(date);
                  final isWeekend = date.weekday == DateTime.saturday || date.weekday == DateTime.sunday;

                  return _MonthCell(
                    dayNum: dayNum,
                    isToday: isToday,
                    isSelected: isSelected,
                    isWeekend: isWeekend,
                    events: dayEvts,
                    onTap: () {
                      setState(() => _focusDate = date);
                    },
                    onAddTap: () => _showAddEventDialog(date),
                    onEventTap: (evt) => _confirmDelete(evt['id'].toString()),
                  );
                },
              );
            },
          ),
        ),
      ]),
    );
  }

  Widget _emptyMonthCell(int n, int col) {
    final isWeekend = col == 0 || col == 6;
    return Container(
      decoration: BoxDecoration(
        color: isWeekend
            ? Colors.black.withValues(alpha: 0.15)
            : Colors.black.withValues(alpha: 0.08),
        border: Border(
          right: BorderSide(color: Colors.white.withValues(alpha: 0.05)),
          bottom: BorderSide(color: Colors.white.withValues(alpha: 0.05)),
        ),
      ),
      alignment: Alignment.topRight,
      padding: const EdgeInsets.all(8),
      child: Text('$n',
          style: TextStyle(
              fontSize: 12,
              color: Colors.white.withValues(alpha: 0.15))),
    );
  }

  // ████████████████████████  WEEK VIEW  ████████████████████████████████████

  Widget _buildWeekView() {
    return PageView.builder(
      controller: _weekPageCtrl,
      physics: const PageScrollPhysics(parent: ClampingScrollPhysics()),
      scrollDirection: Axis.horizontal,
      onPageChanged: (idx) {
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
              events: _events,
              onEventTap: (e) => _confirmDelete(e['id'].toString())),
          dayCount: 7,
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
        );
      },
    );
  }

  // ── Shared time-grid scaffold ────────────────────────────────────────────
  Widget _buildTimeGridView({
    required List<Widget> dayHeaders,
    required Widget eventLayer,
    required int dayCount,
  }) {
    const hours = [
      '12 AM', '1 AM', '2 AM', '3 AM', '4 AM', '5 AM', '6 AM', '7 AM', '8 AM', '9 AM', '10 AM', '11 AM',
      '12 PM', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM', '6 PM', '7 PM', '8 PM', '9 PM', '10 PM', '11 PM',
    ];
    const hourH = 60.0;

    return _glassPanel(
      child: Column(children: [
        // Day header row
        Row(children: [
          const SizedBox(width: 64),
          ...dayHeaders.map((h) => Expanded(child: h)),
        ]),
        Container(height: 1, color: Colors.white.withValues(alpha: 0.06)),
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
                    // Current time line
                    _CurrentTimeLine(
                        dayCount: dayCount,
                        startHour: 0,
                        hourH: hourH),
                  ]),
                ),
              ]),
            ),
          ),
        ),
      ]),
    );
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
          events: _events,
          onDayTap: (d) {
            setState(() => _focusDate = d);
            if (_view == CalView.month) {
              // if month changed, refetch
              if (d.month != _focusDate.month || d.year != _focusDate.year) {
                _fetchEvents();
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
                          borderRadius: BorderRadius.circular(10),
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
          borderRadius: BorderRadius.circular(10),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.06),
              borderRadius: BorderRadius.circular(10),
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
  final int dayNum;
  final bool isToday, isSelected, isWeekend;
  final List<dynamic> events;
  final VoidCallback onTap;
  final VoidCallback onAddTap;
  final void Function(dynamic evt) onEventTap;

  const _MonthCell({
    required this.dayNum,
    required this.isToday,
    required this.isSelected,
    required this.isWeekend,
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
            Padding(
              padding:
                  const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Day number
                    Row(children: [
                      const Spacer(),
                      widget.isToday
                          ? Container(
                              width: 26,
                              height: 26,
                              decoration: BoxDecoration(
                                color: Colors.white,
                                shape: BoxShape.circle,
                                boxShadow: [
                                  BoxShadow(
                                      color: Colors.white
                                          .withValues(alpha: 0.4),
                                      blurRadius: 12)
                                ],
                              ),
                              alignment: Alignment.center,
                              child: Text('${widget.dayNum}',
                                  style: const TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.black)),
                            )
                          : Text('${widget.dayNum}',
                              style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w500,
                                  color: widget.isWeekend
                                      ? Colors.white38
                                      : Colors.white60)),
                    ]),
                    const SizedBox(height: 4),
                    // Events (up to 2, then +N)
                    ...widget.events.take(2).map((e) {
                      final c = _eventColor(e['summary']?.toString());
                      return Container(
                        margin: const EdgeInsets.only(bottom: 2),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 5, vertical: 2),
                        decoration: BoxDecoration(
                          color: c.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(4),
                          border: Border(
                              left: BorderSide(color: c, width: 2)),
                        ),
                        child: Text(e['summary'] ?? 'Event',
                            style: const TextStyle(
                                fontSize: 9,
                                color: Colors.white,
                                fontWeight: FontWeight.w500),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis),
                      );
                    }),
                    if (widget.events.length > 2)
                      Text('+${widget.events.length - 2} more',
                          style: const TextStyle(
                              fontSize: 9, color: Colors.white38)),
                  ]),
            ),
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
                fontSize: 9,
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

        // Events
        ...events.expand((e) {
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

          final colIdx = days.indexWhere((d) =>
              d.year == startDt.year &&
              d.month == startDt.month &&
              d.day == startDt.day);
          if (colIdx < 0) return <Widget>[];

          final startMin =
              (startDt.hour - startHour) * 60 + startDt.minute;
          final durMin = endDt.difference(startDt).inMinutes;
          final top = startMin / 60 * hourH;
          final height = (durMin / 60 * hourH).clamp(20.0, double.infinity);

          final color = _eventColor(e['summary']?.toString());

          return [
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
                            '${DateFormat('h:mm a').format(startDt)} – ${DateFormat('h:mm a').format(endDt)}',
                            style: const TextStyle(
                                fontSize: 9,
                                color: Colors.white54),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis),
                      ]),
                ),
              ),
            ),
          ];
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
        ...events.expand((e) {
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

          final startMin =
              (startDt.hour - startHour) * 60 + startDt.minute;
          final durMin = endDt.difference(startDt).inMinutes;
          final top = startMin / 60 * hourH;
          final height = (durMin / 60 * hourH).clamp(24.0, double.infinity);
          final color = _eventColor(e['summary']?.toString());

          return [
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
                              '${DateFormat('h:mm a').format(startDt)} – ${DateFormat('h:mm a').format(endDt)}',
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
          ];
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
      top: top,
      left: 0,
      right: 0,
      child: Row(children: [
        Container(
            width: 9,
            height: 9,
            decoration: BoxDecoration(
                color: Colors.redAccent, 
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                      color: Colors.redAccent.withValues(alpha: 0.5), 
                      blurRadius: 6, 
                      spreadRadius: 2)
                ])),
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
            duration: const Duration(milliseconds: 300),
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
