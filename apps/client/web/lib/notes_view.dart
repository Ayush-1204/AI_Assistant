import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'providers/data_providers.dart';

class NotesView extends ConsumerWidget {
  const NotesView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notesAsyncValue = ref.watch(notesProvider);
    
    return Stack(
      children: [
        // Background Glows
        Positioned(
          top: -100,
          left: -100,
          child: Container(
            width: 400,
            height: 400,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Colors.white.withOpacity(0.015),
              boxShadow: [BoxShadow(color: Colors.white.withOpacity(0.015), blurRadius: 120)],
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
                  const Text('AI Research Notes', style: TextStyle(
                    fontSize: 28, fontWeight: FontWeight.w600,
                    letterSpacing: -0.5, color: Colors.white
                  )),
                  const Spacer(),
                  Container(
                    decoration: BoxDecoration(
                      boxShadow: [BoxShadow(color: Colors.white.withOpacity(0.1), blurRadius: 16)],
                    ),
                    child: ElevatedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.add, size: 18),
                      label: const Text('New Note'),
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
              // Notes Grid
              Expanded(
                child: notesAsyncValue.when(
                  loading: () => const Center(child: CircularProgressIndicator(color: Colors.white)),
                  error: (err, stack) => Center(child: Text('Error loading notes: $err', style: const TextStyle(color: Colors.redAccent))),
                  data: (notes) {
                    if (notes.isEmpty) {
                      return Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.description_outlined, size: 48, color: Colors.white.withOpacity(0.2)),
                            const SizedBox(height: 16),
                            Text('No notes found.', style: TextStyle(color: Colors.white.withOpacity(0.5))),
                          ],
                        )
                      );
                    }
                    return GridView.builder(
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 3,
                        crossAxisSpacing: 24,
                        mainAxisSpacing: 24,
                        childAspectRatio: 1.1,
                      ),
                      itemCount: notes.length,
                      itemBuilder: (context, index) {
                        return _NoteItemCard(notes[index], index);
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

class _NoteItemCard extends StatefulWidget {
  final dynamic note;
  final int index;
  
  const _NoteItemCard(this.note, this.index);

  @override
  State<_NoteItemCard> createState() => _NoteItemCardState();
}

class _NoteItemCardState extends State<_NoteItemCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0, end: 1),
      duration: Duration(milliseconds: 300 + (widget.index * 100)),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) {
        return Transform.translate(
          offset: Offset(0, 30 * (1 - value)),
          child: Opacity(
            opacity: value,
            child: MouseRegion(
              onEnter: (_) => setState(() => _isHovered = true),
              onExit: (_) => setState(() => _isHovered = false),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                decoration: BoxDecoration(
                  color: const Color(0xFF1F1F1F).withOpacity(0.7),
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: Colors.white.withOpacity(_isHovered ? 0.2 : 0.05)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(_isHovered ? 0.4 : 0.2), 
                      blurRadius: _isHovered ? 24 : 10, 
                      offset: Offset(0, _isHovered ? 10 : 4)
                    )
                  ],
                ),
                child: Material(
                  color: Colors.transparent,
                  child: InkWell(
                    onTap: () {},
                    borderRadius: BorderRadius.circular(24),
                    child: Padding(
                      padding: const EdgeInsets.all(24.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.description, size: 16, color: Colors.white.withOpacity(0.7)),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  widget.note['title'] ?? 'Untitled Note',
                                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Colors.white),
                                  maxLines: 1, overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Expanded(
                            child: Text(
                              widget.note['content'] ?? 'Empty note content...',
                              style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 13, height: 1.5),
                              maxLines: 4, overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(4), border: Border.all(color: Colors.white.withOpacity(0.1))),
                                child: Text('AI Research', style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.7))),
                              ),
                              const Spacer(),
                              Text('Just now', style: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 11)),
                            ],
                          )
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
