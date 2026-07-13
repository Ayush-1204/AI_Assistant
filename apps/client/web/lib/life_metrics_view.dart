import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class LifeMetricsView extends ConsumerWidget {
  const LifeMetricsView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('Life Metrics', style: TextStyle(
                fontSize: 28, fontWeight: FontWeight.w600,
                letterSpacing: -0.5, color: Colors.white
              )),
              Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  gradient: LinearGradient(colors: [Colors.blueAccent.shade400, Colors.lightBlueAccent]),
                  boxShadow: [BoxShadow(color: Colors.lightBlueAccent.withValues(alpha: 0.3), blurRadius: 12, offset: const Offset(0, 4))],
                ),
                child: ElevatedButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.add, size: 16, color: Colors.white),
                  label: const Text('Add Metric', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.transparent,
                    shadowColor: Colors.transparent,
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              )
            ],
          ),
          const SizedBox(height: 8),
          Text('Track habits and expenses natively extracted by the AI.', style: TextStyle(fontSize: 15, color: Colors.grey[500])),
          const SizedBox(height: 32),
          
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── Habits Column ──
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.check_circle_outline, color: Colors.greenAccent, size: 20),
                        SizedBox(width: 8),
                        Text('Active Habits', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                      ],
                    ),
                    const SizedBox(height: 16),
                    _buildMetricCard(
                      child: Column(
                        children: [
                          _buildHabitRow('Morning Run', 3, true),
                          const Divider(color: Colors.white12, height: 24),
                          _buildHabitRow('Read 10 Pages', 7, true),
                          const Divider(color: Colors.white12, height: 24),
                          _buildHabitRow('Meditation', 0, false),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 24),
              // ── Expenses Column ──
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.receipt_long, color: Colors.amberAccent, size: 20),
                        SizedBox(width: 8),
                        Text('Recent Expenses', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white)),
                      ],
                    ),
                    const SizedBox(height: 16),
                    _buildMetricCard(
                      child: Column(
                        children: [
                          _buildExpenseRow('Coffee Shop', 4.50, 'Food & Drink', 'Today'),
                          const Divider(color: Colors.white12, height: 24),
                          _buildExpenseRow('Uber Ride', 18.20, 'Transport', 'Yesterday'),
                          const Divider(color: Colors.white12, height: 24),
                          _buildExpenseRow('AWS Hosting', 12.00, 'Cloud Services', 'Oct 23'),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildHabitRow(String title, int streak, bool doneToday) {
    return Row(
      children: [
        Container(
          width: 20, height: 20,
          decoration: BoxDecoration(
            color: doneToday ? Colors.greenAccent.withValues(alpha: 0.2) : Colors.white10,
            shape: BoxShape.circle,
            border: Border.all(color: doneToday ? Colors.greenAccent : Colors.white24, width: 1.5),
          ),
          child: doneToday ? const Icon(Icons.check, size: 12, color: Colors.greenAccent) : null,
        ),
        const SizedBox(width: 12),
        Expanded(child: Text(title, style: TextStyle(fontSize: 15, color: Colors.white.withValues(alpha: 0.9), fontWeight: FontWeight.w600))),
        if (streak > 0)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.orangeAccent.withValues(alpha: 0.12), 
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.orangeAccent.withValues(alpha: 0.3))
            ),
            child: Row(
              children: [
                const Icon(Icons.local_fire_department, size: 14, color: Colors.orangeAccent),
                const SizedBox(width: 4),
                Text('$streak days', style: const TextStyle(color: Colors.orangeAccent, fontSize: 13, fontWeight: FontWeight.bold)),
              ],
            ),
          )
      ],
    );
  }

  Widget _buildExpenseRow(String merchant, double amount, String category, String date) {
    return _HoverScaleItem(
      child: Row(
        children: [
          Container(
            width: 42, height: 42,
            decoration: BoxDecoration(
              gradient: LinearGradient(colors: [Colors.amberAccent.withValues(alpha: 0.2), Colors.orangeAccent.withValues(alpha: 0.1)]),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.amberAccent.withValues(alpha: 0.3))
            ),
            child: const Icon(Icons.attach_money, size: 20, color: Colors.amberAccent),
          ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(merchant, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Colors.white)),
              const SizedBox(height: 4),
              Text('$category • $date', style: const TextStyle(fontSize: 12, color: Colors.white54)),
            ],
          ),
        ),
        Text('\$${amount.toStringAsFixed(2)}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
      ],
    ),
    );
  }

  Widget _buildMetricCard({required Widget child}) {
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
}

class _HoverScaleItem extends StatefulWidget {
  final Widget child;
  const _HoverScaleItem({required this.child});
  @override
  State<_HoverScaleItem> createState() => _HoverScaleItemState();
}

class _HoverScaleItemState extends State<_HoverScaleItem> {
  bool _isHovered = false;
  
  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: AnimatedScale(
        scale: _isHovered ? 1.02 : 1.0,
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOutCubic,
        child: widget.child,
      ),
    );
  }
}
