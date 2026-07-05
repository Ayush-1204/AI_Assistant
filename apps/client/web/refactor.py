import re

path = r'c:\Users\AYUSH VERMA\Documents\AI_Assistant\apps\client\web\lib\chat_view.dart'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_grid = """        return GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: crossAxisCount,
          crossAxisSpacing: 24,
          mainAxisSpacing: 24,
          childAspectRatio: 1.5,
          children: widgets.asMap().entries.map((entry) {
            final i = entry.key;
            final w = entry.value;
            // Map simple color hex safely
            Color color = Colors.white;
            try {
              if (w['color_hex'] != null) color = Color(int.parse(w['color_hex'], radix: 16));
            } catch (_) {}
            
            // Map icon (we just use a default fallback for now)
            IconData icon = Icons.dashboard;
            if (w['id'] == 'weather') icon = Icons.cloud;
            if (w['id'] == 'calendar') icon = Icons.calendar_month;
            if (w['id'] == 'news') icon = Icons.public;
            
            return _DashboardWidgetCard(
              icon, color, w['badge'] ?? '', w['title'] ?? '', w['subtitle'] ?? '', i
            );
          }).toList(),
        );"""

new_grid = """        return GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: crossAxisCount,
          crossAxisSpacing: 24,
          mainAxisSpacing: 24,
          childAspectRatio: 1.1,
          children: widgets.asMap().entries.map((entry) {
            return _DashboardWidgetCard(data: entry.value, index: entry.key);
          }).toList(),
        );"""

if old_grid in content:
    content = content.replace(old_grid, new_grid)
else:
    # Use regex
    regex = r'Widget _buildDashboardWidgets\(\) \{.*?\}(?=\n\n  @override\n  Widget build)'
    match = re.search(regex, content, re.DOTALL)
    if match:
        new_func = """Widget _buildDashboardWidgets() {
    final screenWidth = MediaQuery.of(context).size.width;
    int crossAxisCount = screenWidth > 1200 ? 3 : (screenWidth > 800 ? 2 : 1);
    return FutureBuilder<List<dynamic>>(
      future: ref.read(apiClientProvider).fetchDashboardWidgets(),
      builder: (context, snapshot) {
        if (!snapshot.hasData || snapshot.data!.isEmpty) {
          return const SizedBox(height: 24, child: Center(child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)));
        }
        final widgets = snapshot.data!;
        return GridView.count(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisCount: crossAxisCount,
          crossAxisSpacing: 24,
          mainAxisSpacing: 24,
          childAspectRatio: 1.1,
          children: widgets.asMap().entries.map((entry) {
            return _DashboardWidgetCard(data: entry.value, index: entry.key);
          }).toList(),
        );
      }
    );
  }"""
        content = content.replace(match.group(0), new_func)

old_card = """class _DashboardWidgetCard extends StatefulWidget {
  final IconData icon;
  final Color color;
  final String badge;
  final String title;
  final String subtitle;
  final int index;
  
  const _DashboardWidgetCard(this.icon, this.color, this.badge, this.title, this.subtitle, this.index);

  @override
  State<_DashboardWidgetCard> createState() => _DashboardWidgetCardState();
}"""

new_card = """class _DashboardWidgetCard extends StatefulWidget {
  final Map<String, dynamic> data;
  final int index;
  const _DashboardWidgetCard({Key? key, required this.data, required this.index}) : super(key: key);
  @override
  State<_DashboardWidgetCard> createState() => _DashboardWidgetCardState();
}"""
content = content.replace(old_card, new_card)


state_idx = content.find("class _DashboardWidgetCardState extends State<_DashboardWidgetCard> {")
if state_idx != -1:
    content = content[:state_idx] + """class _DashboardWidgetCardState extends State<_DashboardWidgetCard> {
  bool _isHovered = false;
  late PageController _pageController;

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

  Widget _buildWeatherInner() {
    final w = widget.data;
    final forecast = w['forecast'] as List<dynamic>? ?? [];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(w['title'] ?? '', style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.white, height: 1.0)),
                const SizedBox(height: 4),
                Text(w['subtitle'] ?? '', style: TextStyle(fontSize: 13, color: Colors.white.withOpacity(0.5))),
              ],
            ),
            const Icon(Icons.cloud, size: 48, color: Colors.amberAccent),
          ],
        ),
        const SizedBox(height: 16),
        Text(w['ai_summary'] ?? '', style: TextStyle(fontSize: 13, height: 1.4, color: Colors.white.withOpacity(0.8)), maxLines: 3, overflow: TextOverflow.ellipsis),
        const Spacer(),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: forecast.map((f) {
            return Column(
              children: [
                Text(f['day'].toString(), style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.5))),
                const SizedBox(height: 4),
                Icon(Icons.wb_sunny, size: 16, color: Colors.white.withOpacity(0.8)),
                const SizedBox(height: 4),
                Text("${f['high']}°", style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white)),
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
                Text(w['title'] ?? '', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
                Text(w['badge'] ?? '', style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.5))),
              ],
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(color: Colors.indigoAccent.withOpacity(0.2), borderRadius: BorderRadius.circular(12)),
              child: const Text('Today', style: TextStyle(color: Colors.indigoAccent, fontSize: 11, fontWeight: FontWeight.bold)),
            )
          ],
        ),
        const SizedBox(height: 12),
        Text(w['ai_summary'] ?? '', style: TextStyle(fontSize: 13, height: 1.4, color: Colors.white.withOpacity(0.8)), maxLines: 2, overflow: TextOverflow.ellipsis),
        const Spacer(),
        SizedBox(
          height: 120,
          child: GridView.builder(
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 7, childAspectRatio: 1.0, mainAxisSpacing: 4, crossAxisSpacing: 4
            ),
            itemCount: grid.length,
            itemBuilder: (context, idx) {
              final d = grid[idx];
              if (d['day'] == 0) return const SizedBox();
              bool isEvent = d['hasEvent'] ?? false;
              bool isToday = d['day'] == w['current_day'];
              return Container(
                decoration: BoxDecoration(
                  color: isToday ? Colors.indigoAccent : (isEvent ? Colors.white.withOpacity(0.08) : Colors.transparent),
                  borderRadius: BorderRadius.circular(6),
                ),
                alignment: Alignment.center,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(d['day'].toString(), style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(isToday ? 1.0 : 0.5))),
                    if (isEvent && !isToday) Container(margin: const EdgeInsets.only(top: 2), width: 4, height: 4, decoration: const BoxDecoration(color: Colors.indigoAccent, shape: BoxShape.circle)),
                  ],
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildNewsInner() {
    final w = widget.data;
    final articles = w['articles'] as List<dynamic>? ?? [];
    if (articles.isEmpty) return const SizedBox();
    return Stack(
      children: [
        PageView.builder(
          controller: _pageController,
          itemBuilder: (context, idx) {
            final actIdx = idx % articles.length; // infinite scroll math
            final article = articles[actIdx];
            return Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(color: Colors.green.withOpacity(0.2), borderRadius: BorderRadius.circular(6)),
                    child: Text(article['domain'].toString().toUpperCase(), style: const TextStyle(color: Colors.greenAccent, fontSize: 10, fontWeight: FontWeight.bold)),
                  ),
                  const SizedBox(height: 12),
                  Text(article['title'] ?? '', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white, height: 1.2), maxLines: 2, overflow: TextOverflow.ellipsis),
                  const SizedBox(height: 8),
                  Text(article['summary'] ?? '', style: TextStyle(fontSize: 13, height: 1.4, color: Colors.white.withOpacity(0.6)), maxLines: 4, overflow: TextOverflow.ellipsis),
                ],
              ),
            );
          },
        ),
        Positioned(
          bottom: 0, right: 0,
          child: Row(
            children: [
              IconButton(icon: Icon(Icons.chevron_left, color: Colors.white.withOpacity(0.5)), onPressed: () { _pageController.previousPage(duration: const Duration(milliseconds: 300), curve: Curves.ease); }),
              IconButton(icon: Icon(Icons.chevron_right, color: Colors.white.withOpacity(0.5)), onPressed: () { _pageController.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.ease); }),
            ],
          )
        )
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
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
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1F1F1F).withOpacity(0.6),
                    borderRadius: BorderRadius.circular(32),
                    border: Border.all(color: Colors.white.withOpacity(_isHovered ? 0.2 : 0.05)),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(_isHovered ? 0.4 : 0.2), 
                        blurRadius: _isHovered ? 24 : 10, 
                        offset: Offset(0, _isHovered ? 10 : 4)
                      )
                    ],
                  ),
                  child: id == 'weather' ? _buildWeatherInner()
                       : id == 'calendar' ? _buildCalendarInner()
                       : id == 'news' ? _buildNewsInner()
                       : const SizedBox(),
                ),
              ),
            ),
          ),
        );
      }
    );
  }
}
"""

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Execution success')
