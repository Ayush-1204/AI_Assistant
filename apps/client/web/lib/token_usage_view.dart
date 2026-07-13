import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';

final tokenBudgetsProvider = FutureProvider<List<dynamic>>((ref) async {
  final dio = Dio(BaseOptions(baseUrl: 'http://localhost:8000'));
  final response = await dio.get('/dashboard/budgets');
  return response.data as List<dynamic>;
});

class TokenUsageView extends ConsumerWidget {
  const TokenUsageView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final budgetsAsyncValue = ref.watch(tokenBudgetsProvider);
    
    return Stack(
      children: [
        // Background Glows
        Positioned(
          top: -100,
          right: -100,
          child: Container(
            width: 400,
            height: 400,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Colors.white.withValues(alpha: 0.015),
              boxShadow: [BoxShadow(color: Colors.white.withValues(alpha: 0.015), blurRadius: 120)],
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                children: [
                   const Text('Live Token Analytics', style: TextStyle(
                    fontSize: 28, fontWeight: FontWeight.w600,
                    letterSpacing: -0.5, color: Colors.white
                  )),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.refresh, color: Colors.white),
                    onPressed: () => ref.refresh(tokenBudgetsProvider),
                  )
                ],
              ),
              const SizedBox(height: 32),
              Expanded(
                child: budgetsAsyncValue.when(
                  loading: () => const Center(child: CircularProgressIndicator(color: Colors.white)),
                  error: (err, stack) => Center(child: Text('Error loading budgets: $err', style: const TextStyle(color: Colors.redAccent))),
                  data: (budgets) {
                    if (budgets.isEmpty) {
                      return Center(
                        child: Text('No active budgets mapped.', style: TextStyle(color: Colors.white.withValues(alpha: 0.5))),
                      );
                    }
                    return ListView.builder(
                      itemCount: budgets.length,
                      itemBuilder: (context, index) {
                        final b = budgets[index];
                        return _BudgetCard(b);
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _BudgetCard extends StatefulWidget {
  final dynamic budget;
  const _BudgetCard(this.budget);

  @override
  State<_BudgetCard> createState() => _BudgetCardState();
}

class _BudgetCardState extends State<_BudgetCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final name = widget.budget['provider'] ?? 'Unknown';
    final rpmCap = widget.budget['rpm_capacity'] ?? 0;
    final rpmRem = widget.budget['rpm_remaining'] ?? 0;
    final tpmCap = widget.budget['tpm_capacity'] ?? 0;
    final tpmRem = widget.budget['tpm_remaining'] ?? 0;
    
    double rpmPct = rpmCap > 0 ? (rpmCap - rpmRem) / rpmCap : 0;
    double tpmPct = tpmCap > 0 ? (tpmCap - tpmRem) / tpmCap : 0;
    if (rpmPct < 0) rpmPct = 0; if (rpmPct > 1) rpmPct = 1;
    if (tpmPct < 0) tpmPct = 0; if (tpmPct > 1) tpmPct = 1;

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.only(bottom: 24),
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: const Color(0xFF1F1F1F).withValues(alpha: 0.7),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.white.withValues(alpha: _isHovered ? 0.2 : 0.05)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: _isHovered ? 0.4 : 0.2), 
              blurRadius: _isHovered ? 24 : 10, 
              offset: Offset(0, _isHovered ? 10 : 4)
            )
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.hub, color: Colors.white.withValues(alpha: 0.8), size: 18),
                const SizedBox(width: 8),
                Text(
                  name.toString().toUpperCase(), 
                  style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 1.1)
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(color: Colors.greenAccent.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(8)),
                  child: Text('\$${(widget.budget['total_cost'] ?? 0.0).toStringAsFixed(6)}', style: const TextStyle(color: Colors.greenAccent, fontSize: 13, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
                )
              ],
            ),
            const SizedBox(height: 24),
            _buildBar('Requests Per Minute (RPM)', rpmRem, rpmCap, rpmPct),
            const SizedBox(height: 20),
            _buildBar('Tokens Per Minute (TPM)', tpmRem, tpmCap, tpmPct),
          ],
        ),
      ),
    );
  }

  Widget _buildBar(String title, num remaining, num capacity, double pct) {
    final bool isWarning = pct > 0.8;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title, style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 13, fontWeight: FontWeight.w500)),
            Text('${capacity - remaining} / $capacity', style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 12, fontFamily: 'monospace')),
          ],
        ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: pct,
            minHeight: 8,
            backgroundColor: Colors.white.withValues(alpha: 0.05),
            color: isWarning ? Colors.redAccent : Colors.white.withValues(alpha: 0.8),
          ),
        ),
      ],
    );
  }
}
