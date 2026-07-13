import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'providers/chat_provider.dart';
import 'chat_view.dart';
import 'notes_view.dart';
import 'documents_view.dart';
import 'settings_view.dart';
import 'token_usage_view.dart';
import 'life_metrics_view.dart';
import 'calendar_view.dart';
import 'people_view.dart';
import 'memory_view.dart';

class MainLayout extends StatefulWidget {
  const MainLayout({super.key});

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  int _selectedIndex = 0;
  final ValueNotifier<Offset> _mousePos = ValueNotifier(Offset.zero);
  bool _isSidebarOpen = true;


  final List<Widget> _views = [
    const ChatView(),
    const NotesView(),
    const DocumentsView(),
    const CalendarView(),
    const TokenUsageView(),
    const LifeMetricsView(),
    const PeopleView(),
    const MemoryView(),
    const SettingsView(),
  ];

  static const List<_NavItem> _navItems = [
    _NavItem(icon: Icons.dashboard_outlined, activeIcon: Icons.dashboard, label: 'Workspace'),
    _NavItem(icon: Icons.note_outlined, activeIcon: Icons.note, label: 'Notes'),
    _NavItem(icon: Icons.folder_outlined, activeIcon: Icons.folder, label: 'Knowledge Base'),
    _NavItem(icon: Icons.calendar_month_outlined, activeIcon: Icons.calendar_month, label: 'Calendar'),
    _NavItem(icon: Icons.speed_outlined, activeIcon: Icons.speed, label: 'Token Limits'),
    _NavItem(icon: Icons.track_changes_outlined, activeIcon: Icons.track_changes, label: 'Life Metrics'),
    _NavItem(icon: Icons.people_outline, activeIcon: Icons.people, label: 'People CRM'),
    _NavItem(icon: Icons.psychology_outlined, activeIcon: Icons.psychology, label: 'Memories'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: MouseRegion(
        onHover: (event) {
          _mousePos.value = event.position;
        },
        child: Stack(
          children: [
            Row(
              children: [
                // Sidebar
                AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  curve: Curves.easeOutCubic,
                  width: _isSidebarOpen ? 240 : 72,
                  color: const Color(0xFF0D0D0F),
                  child: ClipRect(
                    child: Column(
                      children: [
                        const SizedBox(height: 28),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        child: Row(
                          mainAxisAlignment: _isSidebarOpen ? MainAxisAlignment.start : MainAxisAlignment.center,
                          children: [
                            if (_isSidebarOpen) ...[
                              Container(
                                width: 32, height: 32,
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: Colors.white.withValues(alpha: 0.15)),
                                  color: Colors.white.withValues(alpha: 0.05),
                                ),
                                child: const Icon(Icons.hub_outlined, size: 16, color: Colors.white),
                              ),
                              const SizedBox(width: 10),
                              const Expanded(child: Text('Second Brain', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Colors.white), maxLines: 1)),
                            ],
                            IconButton(
                              icon: Icon(_isSidebarOpen ? Icons.chevron_left : Icons.menu, color: Colors.white.withValues(alpha: 0.5)),
                              onPressed: () => setState(() => _isSidebarOpen = !_isSidebarOpen),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 28),
                      // Nav items
                      ...List.generate(_navItems.length, (i) {
                        final item = _navItems[i];
                        final selected = _selectedIndex == i;
                        return _SidebarTile(
                          icon: selected ? item.activeIcon : item.icon,
                          label: item.label,
                          selected: selected,
                          isExpanded: _isSidebarOpen,
                          onTap: () => setState(() => _selectedIndex = i),
                        );
                      }),
                      
                      if (_selectedIndex == 0 && _isSidebarOpen) ...[
                        const SizedBox(height: 16),
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 20),
                          child: Align(alignment: Alignment.centerLeft, child: Text('CHAT HISTORY', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white.withValues(alpha: 0.3), letterSpacing: 1.2))),
                        ),
                        const SizedBox(height: 8),
                        Expanded(
                          child: Consumer(
                            builder: (context, ref, child) {
                               final sessions = ref.watch(chatProvider).sessions;
                               if (sessions.isEmpty) return const SizedBox();
                               return ListView.builder(
                                  padding: EdgeInsets.zero,
                                  itemCount: sessions.length,
                                  itemBuilder: (context, i) {
                                     final title = sessions[i]['title']?.toString() ?? 'Session ${sessions[i]['id']}';
                                     final sessionId = sessions[i]['id'] as int;
                                     bool isActive = ref.watch(chatProvider).conversationId == sessionId;
                                     return Padding(
                                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
                                        child: InkWell(
                                          borderRadius: BorderRadius.circular(8),
                                          onTap: () {
                                             ref.read(chatProvider.notifier).switchSession(sessionId);
                                          },
                                          child: Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                                            decoration: BoxDecoration(color: isActive ? Colors.white.withValues(alpha: 0.05) : Colors.transparent, borderRadius: BorderRadius.circular(8)),
                                            child: Row(children: [
                                              Icon(Icons.chat_bubble_outline, size: 14, color: isActive ? Colors.white.withValues(alpha: 0.8) : Colors.white.withValues(alpha: 0.4)),
                                              const SizedBox(width: 12),
                                              Expanded(child: Text(title, style: TextStyle(fontSize: 13, color: isActive ? Colors.white.withValues(alpha: 0.9) : Colors.white.withValues(alpha: 0.6)), maxLines: 1, overflow: TextOverflow.clip)),
                                            ]),
                                          )
                                        ),
                                     );
                                  }
                               );
                            }
                          )
                        ),
                      ] else const Spacer(),
                      Container(height: 1, color: Colors.white.withValues(alpha: 0.06)),
                      _SidebarTile(
                        icon: _selectedIndex == 8 ? Icons.settings : Icons.settings_outlined,
                        label: 'Settings',
                        selected: _selectedIndex == 8,
                        isExpanded: _isSidebarOpen,
                        onTap: () => setState(() => _selectedIndex = 8),
                      ),
                      const SizedBox(height: 12),
                      ],
                    ),
                  ),
                ),
                // Content
                Container(width: 1, color: Colors.white.withValues(alpha: 0.06)),
                Expanded(
                  child: IndexedStack(
                    index: _selectedIndex,
                    children: _views,
                  ),
                ),
              ],
            ),
            Positioned.fill(
              child: IgnorePointer(
                child: ValueListenableBuilder<Offset>(
                  valueListenable: _mousePos,
                  builder: (context, mousePos, child) {
                    return CustomPaint(
                      painter: _SpotlightPainter(mousePos),
                    );
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NavItem {
  final IconData icon;
  final IconData activeIcon;
  final String label;
  const _NavItem({required this.icon, required this.activeIcon, required this.label});
}

class _SidebarTile extends StatefulWidget {
  final IconData icon;
  final String label;
  final bool selected;
  final bool isExpanded;
  final VoidCallback onTap;

  const _SidebarTile({required this.icon, required this.label, required this.selected, this.isExpanded = true, required this.onTap});

  @override
  State<_SidebarTile> createState() => _SidebarTileState();
}

class _SidebarTileState extends State<_SidebarTile> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
      child: MouseRegion(
        onEnter: (_) => setState(() => _isHovered = true),
        onExit: (_) => setState(() => _isHovered = false),
        child: InkWell(
          onTap: widget.onTap,
          borderRadius: BorderRadius.circular(8),
          child: AnimatedScale(
            scale: _isHovered ? 1.02 : 1.0,
            duration: const Duration(milliseconds: 150),
            curve: Curves.easeOutCubic,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                color: widget.selected 
                  ? Colors.white.withValues(alpha: 0.08) 
                  : _isHovered 
                      ? Colors.white.withValues(alpha: 0.03) 
                      : Colors.transparent,
              ),
              child: Row(
                mainAxisAlignment: widget.isExpanded ? MainAxisAlignment.start : MainAxisAlignment.center,
                children: [
                Icon(widget.icon, size: 18, color: widget.selected ? Colors.white : Colors.grey[600]),
                if (widget.isExpanded) ...[
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(widget.label, maxLines: 1, overflow: TextOverflow.clip, style: TextStyle(
                      fontSize: 14,
                      fontWeight: widget.selected ? FontWeight.w500 : FontWeight.w400,
                      color: widget.selected ? Colors.white : Colors.grey[600],
                    )),
                  ),
                ]
              ]),
            ),
          ),
        ),
      ),
    );
  }
}

class _SpotlightPainter extends CustomPainter {
  final Offset mousePos;
  _SpotlightPainter(this.mousePos);

  @override
  void paint(Canvas canvas, Size size) {
    if (mousePos == Offset.zero) return;
    
    final Rect rect = Rect.fromCircle(center: mousePos, radius: 600);
    final Paint paint = Paint()
      ..shader = RadialGradient(
        colors: [
          Colors.white.withValues(alpha: 0.05),
          Colors.transparent,
        ],
        stops: const [0.0, 1.0],
      ).createShader(rect)
      ..blendMode = BlendMode.screen;
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), paint);
  }

  @override
  bool shouldRepaint(covariant _SpotlightPainter oldDelegate) {
    return oldDelegate.mousePos != mousePos;
  }
}
