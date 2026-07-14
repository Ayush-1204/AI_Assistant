import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class PeopleView extends ConsumerWidget {
  const PeopleView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Scaffold structural scaffolding
    final List<Map<String, dynamic>> mockPeople = [
      {'name': 'Sarah Jenkins', 'relation': 'Manager', 'last_interaction': '2 days ago', 'memories': 12, 'notes': 3},
      {'name': 'Alex Rivera', 'relation': 'Co-founder', 'last_interaction': 'Today', 'memories': 54, 'notes': 15},
      {'name': 'Emily Chen', 'relation': 'Sister', 'last_interaction': '1 week ago', 'memories': 20, 'notes': 0},
    ];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('People Directory', style: TextStyle(
                fontSize: 28, fontWeight: FontWeight.w600,
                letterSpacing: -0.5, color: Colors.white
              )),
              const Spacer(),
              _buildFilterChip('All Contacts', true),
              const SizedBox(width: 8),
              _buildFilterChip('Recent', false),
              const SizedBox(width: 8),
              _buildFilterChip('Family', false),
            ],
          ),
          const SizedBox(height: 8),
          Text('Navigating relational context maps detected across your conversations.', style: TextStyle(fontSize: 15, color: Colors.grey[500])),
          const SizedBox(height: 32),
          
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3, 
              crossAxisSpacing: 24, 
              mainAxisSpacing: 24,
              childAspectRatio: 1.6,
            ),
            itemCount: mockPeople.length,
            itemBuilder: (context, index) {
              return _PersonCard(person: mockPeople[index]);
            },
          )
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label, bool active) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: active ? Colors.white.withValues(alpha: 0.1) : Colors.transparent,
        border: Border.all(color: active ? Colors.white.withValues(alpha: 0.2) : Colors.white.withValues(alpha: 0.05)),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(label, style: TextStyle(
        fontSize: 13, 
        color: active ? Colors.white : Colors.white54,
        fontWeight: active ? FontWeight.w600 : FontWeight.w400,
      )),
    );
  }
}

class _PersonCard extends StatefulWidget {
  final Map<String, dynamic> person;
  const _PersonCard({required this.person});

  @override
  State<_PersonCard> createState() => _PersonCardState();
}

class _PersonCardState extends State<_PersonCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final initials = widget.person['name']!.split(' ').map((e) => e[0]).join();

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF141416).withValues(alpha: 0.8),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.white.withValues(alpha: _isHovered ? 0.2 : 0.05)),
          boxShadow: [
            if (_isHovered) BoxShadow(color: Colors.black.withValues(alpha: 0.3), blurRadius: 20, offset: const Offset(0, 10))
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 20,
                  backgroundColor: Colors.blueAccent.withValues(alpha: 0.2),
                  foregroundColor: Colors.blueAccent,
                  child: Text(initials, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(widget.person['name'], style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
                      Text(widget.person['relation'], style: TextStyle(fontSize: 12, color: Colors.blueAccent.withValues(alpha: 0.8))),
                    ],
                  ),
                ),
              ],
            ),
            const Spacer(),
            Container(height: 1, color: Colors.white.withValues(alpha: 0.05)),
            const Spacer(),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildStatIcon(Icons.psychology_outlined, '${widget.person['memories']} Memories'),
                _buildStatIcon(Icons.notes, '${widget.person['notes']} Notes'),
                _buildStatIcon(Icons.access_time_outlined, widget.person['last_interaction']),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildStatIcon(IconData icon, String text) {
    return Row(
      children: [
        Icon(icon, size: 14, color: Colors.white38),
        const SizedBox(width: 4),
        Text(text, style: const TextStyle(fontSize: 11, color: Colors.white54)),
      ],
    );
  }
}
