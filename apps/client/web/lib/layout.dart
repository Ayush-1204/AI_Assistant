import 'package:flutter/material.dart';
import 'chat_view.dart';
import 'notes_view.dart';
import 'documents_view.dart';
import 'settings_view.dart';

class MainLayout extends StatefulWidget {
  const MainLayout({super.key});

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  int _selectedIndex = 0;
  Offset _mousePos = Offset.zero;

  final List<Widget> _views = [
    const ChatView(),
    const NotesView(),
    const DocumentsView(),
    const Center(child: Text('Calendar (Coming Soon)')),
    const SettingsView(),
  ];

  static const List<_NavItem> _navItems = [
    _NavItem(icon: Icons.dashboard_outlined, activeIcon: Icons.dashboard, label: 'Workspace'),
    _NavItem(icon: Icons.note_outlined, activeIcon: Icons.note, label: 'Notes'),
    _NavItem(icon: Icons.folder_outlined, activeIcon: Icons.folder, label: 'Knowledge Base'),
    _NavItem(icon: Icons.calendar_month_outlined, activeIcon: Icons.calendar_month, label: 'Calendar'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: MouseRegion(
        onHover: (event) {
          if (mounted) setState(() => _mousePos = event.position);
        },
        child: Stack(
          children: [
            Row(
              children: [
                // Sidebar
                Container(
                  width: 240,
                  color: const Color(0xFF0D0D0F),
                  child: Column(
                    children: [
                      const SizedBox(height: 28),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 20),
                        child: Row(
                          children: [
                            Container(
                              width: 32, height: 32,
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: Colors.white.withOpacity(0.15)),
                                color: Colors.white.withOpacity(0.05),
                              ),
                              child: const Icon(Icons.hub_outlined, size: 16, color: Colors.white),
                            ),
                            const SizedBox(width: 10),
                            const Text('Second Brain',
                              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Colors.white)),
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
                          onTap: () => setState(() => _selectedIndex = i),
                        );
                      }),
                      const Spacer(),
                      Container(height: 1, color: Colors.white.withOpacity(0.06)),
                      _SidebarTile(
                        icon: _selectedIndex == 4 ? Icons.settings : Icons.settings_outlined,
                        label: 'Settings',
                        selected: _selectedIndex == 4,
                        onTap: () => setState(() => _selectedIndex = 4),
                      ),
                      const SizedBox(height: 12),
                    ],
                  ),
                ),
                // Content
                Container(width: 1, color: Colors.white.withOpacity(0.06)),
                Expanded(child: _views[_selectedIndex]),
              ],
            ),
            Positioned.fill(
              child: IgnorePointer(
                child: CustomPaint(
                  painter: _SpotlightPainter(_mousePos),
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
  final VoidCallback onTap;

  const _SidebarTile({required this.icon, required this.label, required this.selected, required this.onTap});

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
                  ? Colors.white.withOpacity(0.08) 
                  : _isHovered 
                      ? Colors.white.withOpacity(0.03) 
                      : Colors.transparent,
              ),
              child: Row(children: [
                Icon(widget.icon, size: 18, color: widget.selected ? Colors.white : Colors.grey[600]),
                const SizedBox(width: 12),
                Text(widget.label, style: TextStyle(
                  fontSize: 14,
                  fontWeight: widget.selected ? FontWeight.w500 : FontWeight.w400,
                  color: widget.selected ? Colors.white : Colors.grey[600],
                )),
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
          Colors.white.withOpacity(0.05),
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
