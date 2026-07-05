// ignore_for_file: unused_import

import 'package:flutter/material.dart';
import 'dart:ui';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'api_client.dart';
import 'providers/auth_provider.dart';
import 'providers/chat_provider.dart';

class ChatView extends ConsumerStatefulWidget {
  const ChatView({super.key});

  @override
  ConsumerState<ChatView> createState() => _ChatViewState();
}

class _ChatViewState extends ConsumerState<ChatView> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _handleSend(String val) {
    if (val.trim().isEmpty) return;
    ref.read(chatProvider.notifier).sendMessage(val);
    _controller.clear();
    _scrollToBottom();
  }

  Future<void> _pickAndUploadFile() async {
    try {
      FilePickerResult? result = await FilePicker.pickFiles(withData: true);
      if (result != null && result.files.single.bytes != null) {
        final file = result.files.single;
        ref.read(chatProvider.notifier).addMessage("System: Uploading ${file.name}...");
        await ref.read(apiClientProvider).uploadDocument(file.name, file.bytes!, file.name);
        ref.read(chatProvider.notifier).addMessage("System: Successfully uploaded ${file.name} to RAG contextual memory.");
      }
    } catch (e) {
      ref.read(chatProvider.notifier).addMessage("System: Upload failed: $e");
    }
  }


  Widget _buildDashboardWidgets() {
    final screenWidth = MediaQuery.of(context).size.width;
    int crossAxisCount = screenWidth > 1200 ? 3 : (screenWidth > 800 ? 2 : 1);
    
    return FutureBuilder<List<dynamic>>(
      future: ref.read(apiClientProvider).fetchDashboardWidgets(),
      builder: (context, snapshot) {
        if (!snapshot.hasData || snapshot.data!.isEmpty) {
          return GridView.count(
            crossAxisCount: crossAxisCount,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            childAspectRatio: screenWidth > 800 ? 1.45 : 1.75, // Lower ratio = taller cards
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
          childAspectRatio: screenWidth > 800 ? 1.45 : 1.75, // Consistent aspect ratio
          children: List.generate(widgets.length, (index) {
            return _DashboardWidgetCard(
              data: widgets[index] as Map<String, dynamic>,
              index: index
            );
          }),
        );
      },
    );
  }


  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Glassmorphism Header
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.background.withOpacity(0.8),
            border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.05))),
          ),
          child: Row(
            children: [
              const Text('Workspace Overview', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600, letterSpacing: -0.5, color: Colors.white)),
              const Spacer(),
              _buildHeaderAction(Icons.search, "Search"),
              _buildHeaderDivider(),
              Consumer(builder: (context, ref, _) {
                final sessions = ref.watch(chatProvider).sessions;
                return PopupMenuButton<int>(
                  offset: const Offset(0, 40),
                  color: const Color(0xFF1F1F1F),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  onSelected: (id) => ref.read(chatProvider.notifier).switchSession(id),
                  itemBuilder: (context) => sessions.map((s) {
                    final isActive = ref.watch(chatProvider).conversationId == s['id'];
                    return PopupMenuItem<int>(
                      value: s['id'] as int,
                      child: Text(
                        s['title']?.toString() ?? 'Session ${s['id']}',
                        style: TextStyle(color: isActive ? Theme.of(context).colorScheme.primary : Colors.white70),
                      ),
                    );
                  }).toList(),
                  child: _buildHeaderAction(Icons.history, "Recent", active: true),
                );
              }),
              _buildHeaderDivider(),
              _buildHeaderAction(Icons.push_pin, "Pinned"),
              const SizedBox(width: 16),
              IconButton(icon: const Icon(Icons.more_vert), onPressed: () {}, color: Colors.white.withOpacity(0.6)),
            ],
          ),
        ),
        // Threads & Dashboard
        Expanded(
          child: Consumer(builder: (context, ref, child) {
            final chatState = ref.watch(chatProvider);
            return ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(24),
              itemCount: chatState.messages.length + 1,
              itemBuilder: (context, index) {
                if (index == 0) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 32.0),
                    child: _buildDashboardWidgets(),
                  );
                }
                
                final msg = chatState.messages[index - 1];
                final isAssistant = msg.startsWith("Assistant:");
              final displayMsg = isAssistant ? msg.replaceFirst("Assistant:", "").trim() : msg;
              
              return TweenAnimationBuilder<double>(
                key: ValueKey("msg_${chatState.messages.length}_$index"),
                tween: Tween<double>(begin: 0.0, end: 1.0),
                duration: const Duration(milliseconds: 400),
                curve: Curves.easeOutCubic,
                builder: (context, val, child) {
                  return Transform.translate(
                    offset: Offset(0, 10 * (1 - val)),
                    child: Opacity(
                      opacity: val,
                      child: child,
                    ),
                  );
                },
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 24.0),
                  child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: isAssistant ? MainAxisAlignment.start : MainAxisAlignment.end,
                  children: [
                    if (isAssistant)
                      Container(
                        margin: const EdgeInsets.only(right: 16),
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.primary.withOpacity(0.15),
                          shape: BoxShape.circle,
                          border: Border.all(color: Theme.of(context).colorScheme.primary.withOpacity(0.3)),
                        ),
                        child: Icon(Icons.auto_awesome, color: Theme.of(context).colorScheme.primary, size: 20),
                      ),
                    Flexible(
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: isAssistant ? const Color(0xFF1B1B1B).withOpacity(0.9) : const Color(0xFF2A2A2A),
                          borderRadius: BorderRadius.only(
                            topLeft: const Radius.circular(24),
                            topRight: const Radius.circular(24),
                            bottomLeft: isAssistant ? const Radius.circular(4) : const Radius.circular(24),
                            bottomRight: isAssistant ? const Radius.circular(24) : const Radius.circular(4),
                          ),
                          border: Border.all(color: Colors.white.withOpacity(0.05)),
                        ),
                        child: MarkdownBody(
                          data: displayMsg,
                          styleSheet: MarkdownStyleSheet(
                            p: TextStyle(fontSize: 15, height: 1.5, color: Colors.white.withOpacity(0.9)),
                          ),
                        ),
                      ),
                    ),
                    if (!isAssistant)
                      Container(
                        margin: const EdgeInsets.only(left: 16),
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.1),
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white.withOpacity(0.1)),
                        ),
                        child: Icon(Icons.person, color: Colors.white.withOpacity(0.8), size: 20),
                      ),
                  ],
                ),
              ),
            );
          },
            );
          }),
        ),
        // Floating Chat Bar Region
        Consumer(builder: (context, ref, child) {
          final isListening = ref.watch(chatProvider).isListening;
          final isSending = ref.watch(chatProvider).isSending;
          return Container(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
            color: Colors.transparent,
            child: SafeArea(
              child: Align(
                alignment: Alignment.bottomCenter,
                child: Container(
                  constraints: const BoxConstraints(maxWidth: 800),
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF131313).withOpacity(0.95),
                    borderRadius: BorderRadius.circular(32),
                    border: Border.all(color: Colors.white.withOpacity(0.15)),
                    boxShadow: [
                      BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 24, offset: const Offset(0, 10))
                    ],
                  ),
                  child: Row(
                    children: [
                      IconButton(
                        icon: const Icon(Icons.attach_file, size: 22),
                        color: Colors.white.withOpacity(0.6),
                        onPressed: _pickAndUploadFile, 
                      ),
                      const SizedBox(width: 4),
                      Expanded(
                        child: TextField(
                          controller: _controller,
                          style: const TextStyle(fontSize: 15, color: Colors.white),
                          decoration: InputDecoration(
                            hintText: 'Message Aura AI or type "/" for commands...',
                            hintStyle: TextStyle(color: Colors.white.withOpacity(0.4)),
                            border: InputBorder.none,
                            isDense: true,
                            contentPadding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                          onSubmitted: (val) => _handleSend(val),
                        ),
                      ),
                      const SizedBox(width: 4),
                      // Action buttons pill
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.05),
                          borderRadius: BorderRadius.circular(24),
                          border: Border.all(color: Colors.white.withOpacity(0.05)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            IconButton(
                              constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                              padding: EdgeInsets.zero,
                              icon: Icon(isListening ? Icons.mic_off : Icons.mic, size: 20),
                              color: isListening ? Colors.redAccent : Colors.white.withOpacity(0.6),
                              onPressed: () {
                                ref.read(chatProvider.notifier).toggleListening();
                              },
                            ),
                          Container(
                            width: 36,
                            height: 36,
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(18),
                              boxShadow: [BoxShadow(color: Colors.white.withOpacity(0.2), blurRadius: 8)],
                            ),
                            child: IconButton(
                              padding: EdgeInsets.zero,
                              icon: isSending 
                                ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                                : const Icon(Icons.arrow_upward, size: 20),
                              color: Colors.black,
                              onPressed: () => _handleSend(_controller.text),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      }),
      ],
    );
  }

  Widget _buildHeaderAction(IconData icon, String label, {bool active = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          Icon(icon, size: 18, color: active ? Theme.of(context).colorScheme.primary : Colors.white.withOpacity(0.6)),
          const SizedBox(width: 8),
          Text(label, style: TextStyle(
            fontSize: 14, 
            fontWeight: FontWeight.w500, 
            color: active ? Theme.of(context).colorScheme.primary : Colors.white.withOpacity(0.6),
          )),
        ],
      ),
    );
  }

  Widget _buildHeaderDivider() {
    return Container(
      height: 16,
      width: 1,
      color: Colors.white.withOpacity(0.1),
    );
  }
}

class _SkeletonDashboardCard extends StatefulWidget {
  const _SkeletonDashboardCard({super.key});

  @override
  State<_SkeletonDashboardCard> createState() => _SkeletonDashboardCardState();
}

class _SkeletonDashboardCardState extends State<_SkeletonDashboardCard> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  
  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1400))..repeat(reverse: true);
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
        final baseColor = Colors.white.withOpacity(opacity);
        return ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 16.0, sigmaY: 16.0),
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.04),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white.withOpacity(0.08)),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.2), blurRadius: 40, spreadRadius: -10)
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Container(width: 48, height: 48, decoration: BoxDecoration(color: baseColor, shape: BoxShape.circle)),
                      Container(width: 72, height: 24, decoration: BoxDecoration(color: baseColor, borderRadius: BorderRadius.circular(12))),
                    ],
                  ),
                  const SizedBox(height: 20),
                  Container(width: 140, height: 26, decoration: BoxDecoration(color: baseColor, borderRadius: BorderRadius.circular(8))),
                  const SizedBox(height: 12),
                  Container(width: double.infinity, height: 12, decoration: BoxDecoration(color: Colors.white.withOpacity(opacity * 0.7), borderRadius: BorderRadius.circular(4))),
                  const SizedBox(height: 8),
                  Container(width: 180, height: 12, decoration: BoxDecoration(color: Colors.white.withOpacity(opacity * 0.7), borderRadius: BorderRadius.circular(4))),
                  const SizedBox(height: 16),
                  Expanded(
                    child: Container(width: double.infinity, decoration: BoxDecoration(color: Colors.white.withOpacity(opacity * 0.5), borderRadius: BorderRadius.circular(16))),
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
  const AnimatedWeatherIcon({super.key});
  @override
  State<AnimatedWeatherIcon> createState() => _AnimatedWeatherIconState();
}

class _AnimatedWeatherIconState extends State<AnimatedWeatherIcon> with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(vsync: this, duration: const Duration(seconds: 3))..repeat(reverse: true);
  late final Animation<double> _anim = Tween<double>(begin: -8.0, end: 8.0).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOutSine));

  @override
  void dispose() { _controller.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (context, child) => Transform.translate(
        offset: Offset(0, _anim.value),
        child: const Icon(Icons.cloud, size: 48, color: Colors.amberAccent),
      ),
    );
  }
}

class _DashboardWidgetCard extends StatefulWidget {
  final Map<String, dynamic> data;
  final int index;
  const _DashboardWidgetCard({Key? key, required this.data, required this.index}) : super(key: key);
  @override
  State<_DashboardWidgetCard> createState() => _DashboardWidgetCardState();
}

class _DashboardWidgetCardState extends State<_DashboardWidgetCard> {
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
            const AnimatedWeatherIcon(),
          ],
        ),
        if (w['ai_summary'] != null && w['ai_summary'].toString().isNotEmpty) ...[
          const SizedBox(height: 16),
          Expanded(
             child: Text(w['ai_summary'] ?? '', style: TextStyle(fontSize: 13, height: 1.4, color: Colors.white.withOpacity(0.8)), maxLines: 3, overflow: TextOverflow.ellipsis),
          ),
        ] else const Spacer(),
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
        if (w['ai_summary'] != null && w['ai_summary'].toString().isNotEmpty) ...[
          const SizedBox(height: 12),
          Text(w['ai_summary'] ?? '', style: TextStyle(fontSize: 13, height: 1.4, color: Colors.white.withOpacity(0.8)), maxLines: 2, overflow: TextOverflow.ellipsis),
        ],
        const SizedBox(height: 12),
        Expanded(
          child: LayoutBuilder(
            builder: (context, constraints) {
              int rows = (grid.length / 7).ceil();
              if (rows == 0) rows = 1;
              double itemWidth = constraints.maxWidth / 7;
              double itemHeight = constraints.maxHeight / rows;
              double safeRatio = (itemWidth > 0 && itemHeight > 0) ? (itemWidth / itemHeight) : 1.0;

              return GridView.builder(
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 7, 
                  childAspectRatio: safeRatio, 
                  mainAxisSpacing: 4, 
                  crossAxisSpacing: 4
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
                      shape: BoxShape.circle,
                    ),
                    alignment: Alignment.center,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Flexible(child: Text(d['day'].toString(), style: TextStyle(fontSize: 12, fontWeight: isToday ? FontWeight.bold : FontWeight.normal, color: Colors.white.withOpacity(isToday ? 1.0 : 0.6)))),
                        if (isEvent && !isToday) Container(margin: const EdgeInsets.only(top: 2), width: 4, height: 4, decoration: const BoxDecoration(color: Colors.indigoAccent, shape: BoxShape.circle)),
                      ],
                    ),
                  );
                },
              );
            }
          ),
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
                            const Text("Top News", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(color: Colors.green.withOpacity(0.2), borderRadius: BorderRadius.circular(12)),
                              child: Text(article['domain'].toString().toUpperCase(), style: const TextStyle(color: Colors.greenAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Text(article['title'] ?? '', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white, height: 1.2), maxLines: 2, overflow: TextOverflow.ellipsis),
                        const SizedBox(height: 12),
                        Expanded(
                          child: Text(article['summary'] ?? '', style: TextStyle(fontSize: 13, height: 1.6, color: Colors.white.withOpacity(0.6)), overflow: TextOverflow.fade),
                        ),
                        const SizedBox(height: 24), // Avoid crossing over the arrow bounds
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
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(32),
                  child: BackdropFilter(
                    filter: ImageFilter.blur(sigmaX: 16.0, sigmaY: 16.0),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1F1F1F).withOpacity(0.35),
                        borderRadius: BorderRadius.circular(32),
                        border: Border.all(color: Colors.white.withOpacity(_isHovered ? 0.15 : 0.05)),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(_isHovered ? 0.3 : 0.1), 
                            blurRadius: _isHovered ? 24 : 10, 
                            offset: Offset(0, _isHovered ? 8 : 4)
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
            ),
          ),
        );
      }
    );
  }
}
