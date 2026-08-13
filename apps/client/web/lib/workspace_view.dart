import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dart:math';
import 'dart:ui';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:geolocator/geolocator.dart';
import 'providers/chat_provider.dart';
import 'providers/nav_provider.dart';
import 'providers/auth_provider.dart'; // Added this
import 'widgets/chat_input_pill.dart';

class WorkspaceView extends ConsumerStatefulWidget {
  const WorkspaceView({super.key});
  @override
  ConsumerState<WorkspaceView> createState() => _WorkspaceViewState();
}

class _WorkspaceViewState extends ConsumerState<WorkspaceView> {
  late Future<List<dynamic>> _dashboardFuture;
  final TextEditingController _queryController = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Default to an empty future immediately so the UI knows we are loading
    _dashboardFuture = Future.value([]);
    _initDashboard();
  }

  Future<void> _initDashboard() async {
    if (mounted) {
      setState(() {
        _dashboardFuture = ref.read(apiClientProvider).fetchDashboardWidgets();
      });
    }

    // Fetch location in background if already permitted, without aggressively requesting
    _fetchLocationQuietly();
  }

  Future<void> _fetchLocationQuietly() async {
    try {
      if (await Geolocator.isLocationServiceEnabled()) {
        var perm = await Geolocator.checkPermission();
        if (perm == LocationPermission.whileInUse || perm == LocationPermission.always) {
          final pos = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.low);
          ref.read(apiClientProvider).setLocation(pos.latitude, pos.longitude);
          // Optionally refresh dashboard to update weather with exact location
          if (mounted) {
            setState(() {
              _dashboardFuture = ref.read(apiClientProvider).fetchDashboardWidgets();
            });
          }
        }
      }
    } catch (_) {}
  }

  Widget _buildDashboardWidgets() {
    final screenWidth = MediaQuery.of(context).size.width;
    int crossAxisCount = screenWidth > 1200 ? 3 : (screenWidth > 800 ? 2 : 1);

    return FutureBuilder<List<dynamic>>(
      future: _dashboardFuture,
      builder: (context, snapshot) {
        if (!snapshot.hasData || snapshot.data!.isEmpty) {
          return GridView.count(
            crossAxisCount: crossAxisCount,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            childAspectRatio: screenWidth > 800 ? 1.45 : 1.75,
            children: List.generate(3, (index) {
              return const _SkeletonDashboardCard();
            }),
          );
        }

        final widgets = snapshot.data!;
        return GridView.count(
          crossAxisCount: crossAxisCount,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          childAspectRatio: screenWidth > 800 ? 1.45 : 1.75,
          children: List.generate(widgets.length, (index) {
            return _DashboardWidgetCard(
                data: widgets[index] as Map<String, dynamic>, index: index);
          }),
        );
      },
    );
  }

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  void _submitQuery() {
    final text = _queryController.text.trim();
    if (text.isEmpty) return;
    ref.read(chatProvider.notifier).sendMessage(text);
    _queryController.clear();
    ref.read(navIndexProvider.notifier).state = 1; // Go to chat
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF0F0F0F),
      child: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(48.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Workspace', style: TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.w600, letterSpacing: -0.5)),
                  const SizedBox(height: 32),
                  _buildDashboardWidgets(),
                ],
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.only(bottom: 48),
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text("Greetings, Ayush",
                      style: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                          letterSpacing: -0.5)),
                  const SizedBox(height: 12),
                  Text("What's on your mind today?",
                      style: TextStyle(
                          fontSize: 18,
                          color: Colors.white.withValues(alpha: 0.6))),
                  const SizedBox(height: 48),
                  ChatInputPill(
                    controller: _queryController,
                    onSend: () => _submitQuery(),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
class _SkeletonDashboardCard extends StatefulWidget {
  const _SkeletonDashboardCard();

  @override
  State<_SkeletonDashboardCard> createState() => _SkeletonDashboardCardState();
}

class _SkeletonDashboardCardState extends State<_SkeletonDashboardCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1400))
      ..repeat(reverse: true);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (context, child) {
        final opacity = 0.15 + (_ctrl.value * 0.25);
        final baseColor = Colors.white.withValues(alpha: opacity);
        return ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 16.0, sigmaY: 16.0),
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.04),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
                boxShadow: [
                  BoxShadow(
                      color: Colors.black.withValues(alpha: 0.2),
                      blurRadius: 40,
                      spreadRadius: -10)
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                              color: baseColor, shape: BoxShape.circle)),
                      Container(
                          width: 72,
                          height: 24,
                          decoration: BoxDecoration(
                              color: baseColor,
                              borderRadius: BorderRadius.circular(12))),
                    ],
                  ),
                  const SizedBox(height: 20),
                  Container(
                      width: 140,
                      height: 26,
                      decoration: BoxDecoration(
                          color: baseColor,
                          borderRadius: BorderRadius.circular(8))),
                  const SizedBox(height: 12),
                  Container(
                      width: double.infinity,
                      height: 12,
                      decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: opacity * 0.7),
                          borderRadius: BorderRadius.circular(4))),
                  const SizedBox(height: 8),
                  Container(
                      width: 180,
                      height: 12,
                      decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: opacity * 0.7),
                          borderRadius: BorderRadius.circular(4))),
                  const SizedBox(height: 16),
                  Expanded(
                    child: Container(
                        width: double.infinity,
                        decoration: BoxDecoration(
                            color:
                                Colors.white.withValues(alpha: opacity * 0.5),
                            borderRadius: BorderRadius.circular(16))),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class AnimatedWeatherIcon extends StatefulWidget {
  final String condition;
  final double size;
  const AnimatedWeatherIcon({super.key, required this.condition, this.size = 48});
  @override
  State<AnimatedWeatherIcon> createState() => _AnimatedWeatherIconState();
}

class _AnimatedWeatherIconState extends State<AnimatedWeatherIcon>
    with TickerProviderStateMixin {
  late final AnimationController _pulseCtrl;
  late final AnimationController _spinCtrl;
  late final AnimationController _driftCtrl;
  late final AnimationController _rainCtrl;
  
  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(vsync: this, duration: const Duration(seconds: 2))..repeat(reverse: true);
    _spinCtrl = AnimationController(vsync: this, duration: const Duration(seconds: 15))..repeat();
    _driftCtrl = AnimationController(vsync: this, duration: const Duration(seconds: 4))..repeat(reverse: true);
    _rainCtrl = AnimationController(vsync: this, duration: const Duration(seconds: 1))..repeat();
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    _spinCtrl.dispose();
    _driftCtrl.dispose();
    _rainCtrl.dispose();
    super.dispose();
  }

  Widget _buildSun() {
    return AnimatedBuilder(
      animation: Listenable.merge([_spinCtrl, _pulseCtrl]),
      builder: (ctx, _) => Transform.scale(
        scale: 0.95 + (_pulseCtrl.value * 0.05),
        child: Transform.rotate(
          angle: _spinCtrl.value * 2 * 3.14159,
          child: Icon(Icons.wb_sunny, size: widget.size, color: Colors.orangeAccent),
        ),
      ),
    );
  }

  Widget _buildMoon() {
    return AnimatedBuilder(
      animation: _pulseCtrl,
      builder: (ctx, _) => Stack(
        children: [
          Positioned(
            top: widget.size * 0.1, right: widget.size * 0.1,
            child: Icon(Icons.nights_stay, size: widget.size * 0.8, color: Colors.blueAccent.shade100),
          ),
          Positioned(
            top: widget.size * 0.05, left: widget.size * 0.1,
            child: Opacity(opacity: _pulseCtrl.value, child: Icon(Icons.star, size: widget.size * 0.3, color: Colors.yellowAccent)),
          ),
          Positioned(
            left: widget.size * 0.5, bottom: widget.size * 0.15,
            child: Opacity(opacity: 1.0 - _pulseCtrl.value, child: Icon(Icons.star, size: widget.size * 0.2, color: Colors.yellowAccent)),
          ),
        ],
      ),
    );
  }

  Widget _buildCloud({Color color = Colors.white70}) {
    return AnimatedBuilder(
      animation: _driftCtrl,
      builder: (ctx, _) => Transform.translate(
        offset: Offset((_driftCtrl.value - 0.5) * widget.size * 0.15, 0),
        child: Icon(Icons.cloud, size: widget.size, color: color),
      ),
    );
  }

  Widget _buildRain() {
    return Stack(
      children: [
        _buildCloud(color: Colors.white54),
        Positioned.fill(
          child: AnimatedBuilder(
            animation: _rainCtrl,
            builder: (ctx, _) => CustomPaint(
              painter: _RainPainter(progress: _rainCtrl.value, color: Colors.lightBlueAccent, density: 4),
            ),
          ),
        )
      ],
    );
  }

  Widget _buildFog() {
    return Stack(
      children: [
        _buildCloud(color: Colors.white24),
        AnimatedBuilder(
          animation: _pulseCtrl,
          builder: (ctx, _) => Opacity(
            opacity: 0.5 + (_pulseCtrl.value * 0.3),
            child: Icon(Icons.dehaze, size: widget.size, color: Colors.white54),
          ),
        )
      ],
    );
  }

  Widget _buildPartlyCloudy() {
    return Stack(
      children: [
        Positioned(
          top: 0, right: 0,
          child: AnimatedBuilder(
            animation: _spinCtrl,
            builder: (ctx, _) => Transform.rotate(
              angle: _spinCtrl.value * 2 * 3.14159,
              child: Icon(Icons.wb_sunny, size: widget.size * 0.6, color: Colors.orangeAccent),
            ),
          ),
        ),
        Positioned(
            bottom: widget.size * 0.05, left: widget.size * 0.05,
            child: AnimatedBuilder(
              animation: _driftCtrl,
              builder: (ctx, _) => Transform.translate(
                offset: Offset((_driftCtrl.value - 0.5) * widget.size * 0.15, 0),
                child: Icon(Icons.cloud, size: widget.size * 0.75, color: Colors.white70),
              ),
            ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.condition.toLowerCase();
    
    if (c.contains('rain') || c.contains('storm') || c.contains('drizzle') || c.contains('shower')) {
      return SizedBox(width: widget.size, height: widget.size, child: _buildRain());
    } else if (c.contains('fog') || c.contains('mist') || c.contains('haze')) {
      return SizedBox(width: widget.size, height: widget.size, child: _buildFog());
    } else if (c.contains('night') || c.contains('moon')) {
      return SizedBox(width: widget.size, height: widget.size, child: _buildMoon());
    } else if (c.contains('partly') || c.contains('few') || (c.contains('sun') && c.contains('cloud'))) {
      return SizedBox(width: widget.size, height: widget.size, child: _buildPartlyCloudy());
    } else if (c.contains('cloud') || c.contains('overcast')) {
      return SizedBox(width: widget.size, height: widget.size, child: _buildCloud());
    } else if (c.contains('sun') || c.contains('clear')) {
      return SizedBox(width: widget.size, height: widget.size, child: _buildSun());
    }
    
    // Default fallback
    return SizedBox(width: widget.size, height: widget.size, child: _buildPartlyCloudy());
  }
}

class _RainPainter extends CustomPainter {
  final double progress;
  final Color color;
  final int density;
  
  _RainPainter({required this.progress, required this.color, required this.density});
  
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = color
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;
      
    final w = size.width;
    final h = size.height;
    
    for (int i = 0; i < density; i++) {
      final offset = (i / density);
      final yProgress = (progress + offset) % 1.0;
      
      final x = w * (0.2 + (0.6 * (i / (density - 1))));
      final y = h * 0.4 + (h * 0.6 * yProgress); 
      
      canvas.drawLine(Offset(x, y), Offset(x, y + (h * 0.15)), p);
    }
  }

  @override
  bool shouldRepaint(covariant _RainPainter oldDelegate) => true;
}

class _DashboardWidgetCard extends StatefulWidget {
  final Map<String, dynamic> data;
  final int index;
  const _DashboardWidgetCard({required this.data, required this.index});
  @override
  State<_DashboardWidgetCard> createState() => _DashboardWidgetCardState();
}

class _DashboardWidgetCardState extends State<_DashboardWidgetCard>
    with AutomaticKeepAliveClientMixin {
  bool _isHovered = false;
  late PageController _pageController;

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  IconData _getStaticWeatherIcon(String condition) {
    final c = condition.toLowerCase();
    if (c.contains('storm') || c.contains('thunder')) return Icons.thunderstorm;
    if (c.contains('rain') || c.contains('drizzle') || c.contains('shower')) return Icons.water_drop;
    if (c.contains('snow')) return Icons.ac_unit;
    if (c.contains('fog') || c.contains('mist') || c.contains('haze')) return Icons.foggy;
    if (c.contains('night') || c.contains('moon')) return Icons.nights_stay;
    if (c.contains('partly') || c.contains('few') || (c.contains('sun') && c.contains('cloud'))) return Icons.cloud_queue;
    if (c.contains('cloud') || c.contains('overcast')) return Icons.cloud;
    return Icons.wb_sunny;
  }

  Widget _buildWeatherInner() {
    final w = widget.data;
    final forecast = w['forecast'] as List<dynamic>? ?? [];
    final displayCond = w['condition']?.toString() ?? w['subtitle']?.toString() ?? 'Sunny';
    
    String iconCond = displayCond;
    if (w['is_day'] == 0) {
      iconCond += " night";
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (w['location'] != null && w['location'].toString().isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 8.0),
            child: Text(
              w['location'],
              style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: Colors.white),
            ),
          ),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Text(w['title'] ?? '',
                    style: const TextStyle(
                        fontSize: 48,
                        fontWeight: FontWeight.w400,
                        color: Colors.white,
                        letterSpacing: -1.0,
                        height: 1.0)),
                const SizedBox(width: 12),
                AnimatedWeatherIcon(condition: iconCond, size: 42),
              ]
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(displayCond,
                    style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: Colors.white)),
                const SizedBox(height: 4),
                Text(w['subtitle']?.toString() ?? '',
                    style: TextStyle(
                        fontSize: 12,
                        color: Colors.white.withValues(alpha: 0.5))),
              ],
            ),
          ],
        ),
        if (w['ai_summary'] != null && w['ai_summary'].toString().isNotEmpty) ...[
          const SizedBox(height: 16),
          Expanded(
            child: Text(w['ai_summary'] ?? '',
                style: TextStyle(
                    fontSize: 13,
                    height: 1.4,
                    color: Colors.white.withValues(alpha: 0.8)),
                maxLines: 3,
                overflow: TextOverflow.ellipsis),
          ),
        ] else
          const Spacer(),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: forecast.map((f) {
            return Column(
              children: [
                Text(f['day'].toString(),
                    style: TextStyle(
                        fontSize: 11,
                        color: Colors.white.withValues(alpha: 0.5))),
                const SizedBox(height: 6),
                Icon(_getStaticWeatherIcon(f['condition']?.toString() ?? ''),
                    size: 20, color: Colors.white.withValues(alpha: 0.85)),
                const SizedBox(height: 6),
                Text("${f['high']}°",
                    style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.white)),
                if (f['low'] != null && f['low'].toString() != '--')
                  Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text("${f['low']}°",
                        style: TextStyle(
                            fontSize: 12,
                            color: Colors.white.withValues(alpha: 0.5))),
                  ),
              ],
            );
          }).toList(),
        )
      ],
    );
  }

  Widget _buildCalendarInner() {
    final w = widget.data;
    final grid = w['month_grid'] as List<dynamic>? ?? [];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(w['title'] ?? '',
                    style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.white)),
                Text(w['badge'] ?? '',
                    style: TextStyle(
                        fontSize: 12,
                        color: Colors.white.withValues(alpha: 0.5))),
              ],
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                  color: Colors.indigoAccent.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(12)),
              child: const Text('Today',
                  style: TextStyle(
                      color: Colors.indigoAccent,
                      fontSize: 11,
                      fontWeight: FontWeight.bold)),
            )
          ],
        ),
        if (w['ai_summary'] != null &&
            w['ai_summary'].toString().isNotEmpty) ...[
          const SizedBox(height: 12),
          Text(w['ai_summary'] ?? '',
              style: TextStyle(
                  fontSize: 13,
                  height: 1.4,
                  color: Colors.white.withValues(alpha: 0.8)),
              maxLines: 2,
              overflow: TextOverflow.ellipsis),
        ],
        const SizedBox(height: 12),
        Expanded(
          child: LayoutBuilder(builder: (context, constraints) {
            int rows = (grid.length / 7).ceil();
            if (rows == 0) rows = 1;
            double itemWidth = constraints.maxWidth / 7;
            double itemHeight = constraints.maxHeight / rows;
            double safeRatio = (itemWidth > 0 && itemHeight > 0)
                ? (itemWidth / itemHeight)
                : 1.0;

            return GridView.builder(
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 7,
                  childAspectRatio: safeRatio,
                  mainAxisSpacing: 4,
                  crossAxisSpacing: 4),
              itemCount: grid.length,
              itemBuilder: (context, idx) {
                final d = grid[idx];
                if (d['day'] == 0) return const SizedBox();
                bool isEvent = d['hasEvent'] ?? false;
                bool isToday = d['day'] == w['current_day'];
                return Container(
                  decoration: BoxDecoration(
                    color: isToday
                        ? Colors.indigoAccent
                        : (isEvent
                            ? Colors.white.withValues(alpha: 0.08)
                            : Colors.transparent),
                    shape: BoxShape.circle,
                  ),
                  alignment: Alignment.center,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Flexible(
                          child: Text(d['day'].toString(),
                              style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: isToday
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                  color: Colors.white.withValues(
                                      alpha: isToday ? 1.0 : 0.6)))),
                      if (isEvent && !isToday)
                        Container(
                            margin: const EdgeInsets.only(top: 2),
                            width: 4,
                            height: 4,
                            decoration: const BoxDecoration(
                                color: Colors.indigoAccent,
                                shape: BoxShape.circle)),
                    ],
                  ),
                );
              },
            );
          }),
        ),
      ],
    );
  }

  Widget _buildNewsInner() {
    final w = widget.data;
    final articles = w['articles'] as List<dynamic>? ?? [];
    if (articles.isEmpty) return const SizedBox();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
            child: Stack(
          children: [
            PageView.builder(
              controller: _pageController,
              itemBuilder: (context, idx) {
                final actIdx = idx % articles.length;
                final article = articles[actIdx];
                return Padding(
                  padding: const EdgeInsets.only(right: 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text("Top News",
                              style: TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white)),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                                color: Colors.green.withValues(alpha: 0.2),
                                borderRadius: BorderRadius.circular(12)),
                            child: Text(
                                article['domain'].toString().toUpperCase(),
                                style: const TextStyle(
                                    color: Colors.greenAccent,
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(article['title'] ?? '',
                          style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                              height: 1.2),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis),
                      const SizedBox(height: 12),
                      Expanded(
                        child: Text(article['summary'] ?? '',
                            style: TextStyle(
                                fontSize: 13,
                                height: 1.6,
                                color: Colors.white.withValues(alpha: 0.6)),
                            overflow: TextOverflow.fade),
                      ),
                      const SizedBox(
                          height: 24), // Avoid crossing over the arrow bounds
                    ],
                  ),
                );
              },
            ),
            Positioned(
                bottom: 0,
                right: 0,
                child: Row(
                  children: [
                    IconButton(
                        icon: Icon(Icons.chevron_left,
                            color: Colors.white.withValues(alpha: 0.5)),
                        onPressed: () {
                          _pageController.previousPage(
                              duration: const Duration(milliseconds: 300),
                              curve: Curves.ease);
                        }),
                    IconButton(
                        icon: Icon(Icons.chevron_right,
                            color: Colors.white.withValues(alpha: 0.5)),
                        onPressed: () {
                          _pageController.nextPage(
                              duration: const Duration(milliseconds: 300),
                              curve: Curves.ease);
                        }),
                  ],
                ))
          ],
        ))
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    String id = widget.data['id'] ?? '';
    return TweenAnimationBuilder<double>(
        tween: Tween<double>(begin: 0, end: 1),
        duration: Duration(milliseconds: 400 + (widget.index * 150)),
        curve: Curves.easeOutCubic,
        builder: (context, value, child) {
          return Transform.translate(
            offset: Offset(0, 30 * (1 - value)),
            child: Opacity(
              opacity: value,
              child: MouseRegion(
                onEnter: (_) => setState(() => _isHovered = true),
                onExit: (_) => setState(() => _isHovered = false),
                child: AnimatedScale(
                  scale: _isHovered ? 1.02 : 1.0,
                  duration: const Duration(milliseconds: 200),
                  curve: Curves.easeOutCubic,
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(32),
                    child: BackdropFilter(
                      filter: ImageFilter.blur(sigmaX: 16.0, sigmaY: 16.0),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        padding: const EdgeInsets.all(24),
                        decoration: BoxDecoration(
                          color:
                              const Color(0xFF1F1F1F).withValues(alpha: 0.35),
                          borderRadius: BorderRadius.circular(32),
                          border: Border.all(
                              color: Colors.white
                                  .withValues(alpha: _isHovered ? 0.15 : 0.05)),
                          boxShadow: [
                            BoxShadow(
                                color: Colors.black
                                    .withValues(alpha: _isHovered ? 0.3 : 0.1),
                                blurRadius: _isHovered ? 24 : 10,
                                offset: Offset(0, _isHovered ? 8 : 4))
                          ],
                        ),
                        child: id == 'weather'
                            ? _buildWeatherInner()
                            : id == 'calendar'
                                ? _buildCalendarInner()
                                : id == 'news'
                                    ? _buildNewsInner()
                                    : const SizedBox(),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          );
    });
  }
}

