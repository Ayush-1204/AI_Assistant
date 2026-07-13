import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class MemoryView extends ConsumerWidget {
  const MemoryView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Scaffold structural scaffolding
    final List<Map<String, dynamic>> mockPendingDiffs = [
      {'category': 'Preference', 'key': 'Coffee', 'old_value': 'Likes dark roast', 'new_value': 'Switched to decaf only', 'confidence': 0.95},
      {'category': 'Goal', 'key': 'Fitness', 'old_value': null, 'new_value': 'Training for half marathon', 'confidence': 0.88},
    ];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Temporal Knowledge Base', style: TextStyle(
            fontSize: 28, fontWeight: FontWeight.w600,
            letterSpacing: -0.5, color: Colors.white
          )),
          const SizedBox(height: 8),
          Text('Review automated memory diffs extracted dynamically from recent conversational context.', style: TextStyle(fontSize: 15, color: Colors.grey[500])),
          const SizedBox(height: 32),
          
          if (mockPendingDiffs.isNotEmpty) ...[
            const Row(
              children: [
                Icon(Icons.pending_actions, color: Colors.orangeAccent, size: 20),
                SizedBox(width: 8),
                Text('Pending Review', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
              ],
            ),
            const SizedBox(height: 16),
            ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: mockPendingDiffs.length,
              itemBuilder: (context, index) {
                return _MemoryDiffCard(diff: mockPendingDiffs[index]);
              },
            ),
            const SizedBox(height: 32),
          ],
          
          const Row(
            children: [
              Icon(Icons.storage, color: Colors.blueAccent, size: 20),
              SizedBox(width: 8),
              Text('Committed Memories', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
            ],
          ),
          const SizedBox(height: 16),
          // Placeholder for committed items.
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: const Color(0xFF141416).withValues(alpha: 0.8),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
            ),
            child: const Center(
              child: Text('All historical memories are synchronized.', style: TextStyle(color: Colors.white38)),
            ),
          )
        ],
      ),
    );
  }
}

class _MemoryDiffCard extends StatelessWidget {
  final Map<String, dynamic> diff;
  const _MemoryDiffCard({required this.diff});

  @override
  Widget build(BuildContext context) {
    final bool isUpdate = diff['old_value'] != null;

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF141416).withValues(alpha: 0.9),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.orangeAccent.withValues(alpha: 0.2)),
        boxShadow: [BoxShadow(color: Colors.orangeAccent.withValues(alpha: 0.05), blurRadius: 20)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(8)),
                child: Text(diff['category'], style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.bold)),
              ),
              const SizedBox(width: 12),
              Text(diff['key'], style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white)),
              const Spacer(),
              Text('Confidence: ${(diff['confidence'] * 100).toInt()}%', style: TextStyle(color: Colors.greenAccent.withValues(alpha: 0.8), fontSize: 12, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 16),
          if (isUpdate) ...[
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('PREVIOUS STATE', style: TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.1)),
                      const SizedBox(height: 4),
                      Text(diff['old_value'], style: TextStyle(color: Colors.redAccent.withValues(alpha: 0.8), fontSize: 14)),
                    ],
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Icon(Icons.arrow_forward, color: Colors.white.withValues(alpha: 0.2), size: 20),
                ),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('NEW DISCOVERY', style: TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.1)),
                      const SizedBox(height: 4),
                      Text(diff['new_value'], style: TextStyle(color: Colors.greenAccent.withValues(alpha: 0.8), fontSize: 14)),
                    ],
                  ),
                ),
              ],
            )
          ] else ...[
             const Text('NEW DISCOVERY', style: TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.1)),
             const SizedBox(height: 4),
             Text(diff['new_value'], style: TextStyle(color: Colors.greenAccent.withValues(alpha: 0.8), fontSize: 14)),
          ],
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.close, size: 16),
                label: const Text('Reject'),
                style: TextButton.styleFrom(foregroundColor: Colors.white54),
              ),
              const SizedBox(width: 12),
              ElevatedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.check, size: 16),
                label: const Text('Commit to Memory'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orangeAccent.withValues(alpha: 0.2),
                  foregroundColor: Colors.orangeAccent,
                  elevation: 0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
            ],
          )
        ],
      ),
    );
  }
}
