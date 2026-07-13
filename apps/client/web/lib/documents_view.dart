import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'providers/data_providers.dart';

class DocumentsView extends ConsumerWidget {
  const DocumentsView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final docsAsyncValue = ref.watch(documentsProvider);
    return Padding(
      padding: const EdgeInsets.all(32.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('Knowledge Base', style: TextStyle(
                fontSize: 28, fontWeight: FontWeight.w600,
                letterSpacing: -0.5, color: Colors.white
              )),
              const Spacer(),
              Container(
                decoration: BoxDecoration(
                  boxShadow: [BoxShadow(color: Colors.white.withValues(alpha: 0.1), blurRadius: 16)],
                ),
                child: ElevatedButton.icon(
                  onPressed: () {},
                  icon: const Icon(Icons.upload_file, size: 18),
                  label: const Text('Upload Document'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: Colors.black,
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 32),
          Expanded(
            child: Container(
              decoration: BoxDecoration(
                color: const Color(0xFF1F1F1F).withValues(alpha: 0.7),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
                boxShadow: [
                  BoxShadow(color: Colors.black.withValues(alpha: 0.2), blurRadius: 10, offset: const Offset(0, 4))
                ],
              ),
              child: docsAsyncValue.when(
                loading: () => const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator(color: Colors.white))),
                error: (err, stack) => Padding(padding: const EdgeInsets.all(24), child: Center(child: Text('Failed to load documents: $err', style: const TextStyle(color: Colors.redAccent)))),
                data: (docs) {
                  if (docs.isEmpty) {
                    return Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.folder_outlined, size: 48, color: Colors.white.withValues(alpha: 0.2)),
                          const SizedBox(height: 16),
                          Text("No documents in Knowledge Base.", style: TextStyle(color: Colors.white.withValues(alpha: 0.5))),
                        ],
                      )
                    );
                  }
                  return ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: docs.length,
                    separatorBuilder: (_, __) => Divider(color: Colors.white.withValues(alpha: 0.05), height: 1),
                    itemBuilder: (context, index) {
                      final title = docs[index]['filename'] ?? docs[index]['name'] ?? 'Document File';
                      return _DocItemCard(index, title, 'Ready', Icons.description);
                    },
                  );
                }
              ),
            ),
          ),
        ],
      ),
    );
  }

}

class _DocItemCard extends StatefulWidget {
  final int index;
  final String title;
  final String status;
  final IconData icon;

  const _DocItemCard(this.index, this.title, this.status, this.icon);

  @override
  State<_DocItemCard> createState() => _DocItemCardState();
}

class _DocItemCardState extends State<_DocItemCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final bool isReady = widget.status == 'Ready';
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0, end: 1),
      duration: Duration(milliseconds: 300 + (widget.index * 100)),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) {
        return Transform.translate(
          offset: Offset(30 * (1 - value), 0),
          child: Opacity(
            opacity: value,
            child: MouseRegion(
              onEnter: (_) => setState(() => _isHovered = true),
              onExit: (_) => setState(() => _isHovered = false),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                decoration: BoxDecoration(
                  color: _isHovered ? Colors.white.withValues(alpha: 0.04) : Colors.transparent,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: _isHovered ? Colors.white.withValues(alpha: 0.1) : Colors.transparent),
                ),
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: () {},
                    borderRadius: BorderRadius.circular(12),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(8)),
                            child: Icon(widget.icon, color: Colors.white, size: 24),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(widget.title, style: const TextStyle(fontWeight: FontWeight.w600, color: Colors.white, fontSize: 15)),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    Container(width: 8, height: 8, decoration: BoxDecoration(color: isReady ? Colors.greenAccent : Colors.orangeAccent, shape: BoxShape.circle)),
                                    const SizedBox(width: 6),
                                    Text(widget.status, style: TextStyle(color: isReady ? Colors.white.withValues(alpha: 0.6) : Colors.orangeAccent, fontSize: 13)),
                                  ],
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.chat_bubble_outline, size: 20),
                            color: Colors.white.withValues(alpha: 0.6),
                            hoverColor: Colors.white.withValues(alpha: 0.1),
                            tooltip: 'Chat with Document',
                            onPressed: () {},
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        );
      }
    );
  }
}
