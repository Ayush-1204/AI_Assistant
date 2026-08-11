// ignore_for_file: unused_import

import 'package:flutter/material.dart';
import 'dart:ui';
import 'dart:math' as math;
import 'dart:async';
import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_picker/file_picker.dart';
import 'package:geolocator/geolocator.dart';
import 'package:second_brain_frontend/ui/markdown/ai_message_renderer.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:url_launcher/url_launcher_string.dart';
import 'api_client.dart';
import 'providers/auth_provider.dart';
import 'providers/chat_provider.dart';
import 'voice_view.dart';
import 'package:markdown/markdown.dart' as md;
import 'ui/presentation_engine/renderer.dart';
import 'ui/presentation_engine/models.dart';

class CollageSyntax extends md.InlineSyntax {
  CollageSyntax() : super(r'\[COLLAGE:(.*?)\]');

  @override
  bool onMatch(md.InlineParser parser, Match match) {
    if (match.group(1) == null) return false;
    final element = md.Element.text('collage', match.group(1)!);
    parser.addNode(element);
    return true;
  }
}

class CollageElementBuilder extends MarkdownElementBuilder {
  final BuildContext context;
  CollageElementBuilder(this.context);

  Widget _buildImageTile(BuildContext context, String url, int index, List<String> allUrls, {bool isOverlay = false}) {
    final proxyUrl = '${ApiClient.baseUrl}/media/proxy?url=${Uri.encodeComponent(url)}';
    Widget img = Image.network(
      proxyUrl,
      fit: BoxFit.cover,
      headers: const {'Accept': 'image/*'},
      errorBuilder: (context, error, stackTrace) {
        return Image.network(url, fit: BoxFit.cover, 
          errorBuilder: (context, error, stackTrace) {
            return Container(
              color: Colors.grey.withValues(alpha: 0.1),
              child: const Center(
                child: Icon(Icons.image_not_supported_outlined, color: Colors.white54, size: 32)
              )
            );
          });
      },
    );

    if (isOverlay && allUrls.length > 3) {
      img = Stack(
        fit: StackFit.expand,
        children: [
          img,
          Container(
            color: Colors.black.withValues(alpha: 0.6),
            child: Center(
              child: Text(
                '+${allUrls.length - 3}',
                style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ],
      );
    }

    return GestureDetector(
      onTap: () {
        Navigator.of(context).push(
          PageRouteBuilder(
            opaque: false,
            pageBuilder: (BuildContext context, _, __) {
              return _GalleryView(urls: allUrls, initialIndex: index);
            },
          ),
        );
      },
      child: Container(
        clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
          boxShadow: [
            BoxShadow(
                color: Colors.black.withValues(alpha: 0.2),
                blurRadius: 10,
                offset: const Offset(0, 4))
          ],
        ),
        child: img,
      ),
    );
  }

  @override
  Widget visitElementAfter(md.Element element, TextStyle? preferredStyle) {
    var urls = element.textContent.split('||');
    urls = urls.where((u) {
      final lower = u.toLowerCase();
      return !lower.contains('wikimedia.org') && 
             !lower.contains('wikipedia.org') && 
             !lower.contains('unsplash.com');
    }).toList();
    
    if (urls.isEmpty) return const SizedBox.shrink();

    Widget content;
    
    if (urls.length == 1) {
      content = ConstrainedBox(
        constraints: const BoxConstraints(maxHeight: 350),
        child: _buildImageTile(context, urls[0], 0, urls)
      );
    } else if (urls.length == 2) {
      content = SizedBox(
        height: 200,
        child: Row(
          children: [
            Expanded(child: _buildImageTile(context, urls[0], 0, urls)),
            const SizedBox(width: 12),
            Expanded(child: _buildImageTile(context, urls[1], 1, urls)),
          ],
        ),
      );
    } else {
      // 3 or more images - render a row of 3
      content = SizedBox(
        height: 160,
        child: Row(
          children: [
            Expanded(child: _buildImageTile(context, urls[0], 0, urls)),
            const SizedBox(width: 12),
            Expanded(child: _buildImageTile(context, urls[1], 1, urls)),
            const SizedBox(width: 12),
            Expanded(child: _buildImageTile(context, urls[2], 2, urls, isOverlay: true)),
          ],
        ),
      );
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: content,
    );
  }
}

class _GalleryView extends StatefulWidget {
  final List<String> urls;
  final int initialIndex;

  const _GalleryView({required this.urls, required this.initialIndex});

  @override
  State<_GalleryView> createState() => _GalleryViewState();
}

class _GalleryViewState extends State<_GalleryView> {
  late PageController _pageController;

  @override
  void initState() {
    super.initState();
    _pageController = PageController(initialPage: widget.initialIndex);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black87,
      body: Stack(
        children: [
          PageView.builder(
            controller: _pageController,
            itemCount: widget.urls.length,
            itemBuilder: (context, index) {
              final url = widget.urls[index];
              final proxyUrl = '${ApiClient.baseUrl}/media/proxy?url=${Uri.encodeComponent(url)}';
              return InteractiveViewer(
                minScale: 1.0,
                maxScale: 4.0,
                child: Center(
                  child: Image.network(
                    proxyUrl,
                    fit: BoxFit.contain,
                    headers: const {'Accept': 'image/*'},
                    errorBuilder: (context, error, stackTrace) {
                      return Image.network(url, fit: BoxFit.contain,
                        errorBuilder: (context, error, stackTrace) {
                          return const Center(child: Icon(Icons.broken_image, color: Colors.white54, size: 64));
                        },
                      );
                    },
                  ),
                ),
              );
            },
          ),
          Positioned(
            top: 40,
            left: 20,
            child: IconButton(
              icon: const Icon(Icons.close, color: Colors.white, size: 30),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
          Positioned(
            bottom: 40,
            left: 0,
            right: 0,
            child: Center(
                child: GestureDetector(
                  onTap: () async {
                    final currentUrl = widget.urls[_pageController.hasClients ? _pageController.page!.round() : widget.initialIndex];
                    try {
                      await launchUrlString(currentUrl, mode: LaunchMode.externalApplication);
                    } catch (_) {
                      try { await launchUrlString(currentUrl); } catch (_) {}
                    }
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.black54,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: Colors.white24),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.link, color: Colors.white70, size: 16),
                        const SizedBox(width: 8),
                        Text(
                          "Source Image",
                          style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 13),
                        ),
                      ],
                    ),
                  ),
                ),
            ),
          ),
        ],
      ),
    );
  }
}

class LoadingDots extends StatefulWidget {
  const LoadingDots({super.key});
  @override
  State<LoadingDots> createState() => _LoadingDotsState();
}

class _LoadingDotsState extends State<LoadingDots>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1000))
      ..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (i) {
            double offset = 0;
            double progress = (_controller.value * 3) - i;
            if (progress >= 0 && progress <= 1)
              offset = -5 * (0.5 - (progress - 0.5).abs()) * 2;
            return Container(
              margin: const EdgeInsets.symmetric(horizontal: 2),
              transform: Matrix4.translationValues(0, offset, 0),
              width: 6,
              height: 6,
              decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.6),
                  shape: BoxShape.circle),
            );
          }),
        );
      },
    );
  }
}

class ActiveVoiceBar extends ConsumerStatefulWidget {
  const ActiveVoiceBar({super.key});
  @override
  ConsumerState<ActiveVoiceBar> createState() => _ActiveVoiceBarState();
}

class _ActiveVoiceBarState extends ConsumerState<ActiveVoiceBar>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1500))
      ..repeat();
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
        final val = _ctrl.value;
        return Container(
          height: 48,
          decoration: BoxDecoration(
            color: const Color(0xFF2A2A2A),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
          ),
          child: Row(
            children: [
              const SizedBox(width: 12),
              const Icon(Icons.add, color: Colors.white54, size: 18),
              const SizedBox(width: 12),
              Text('.......',
                  style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.2),
                      letterSpacing: 2)),
              const SizedBox(width: 8),
              Expanded(
                child: Consumer(builder: (context, ref, _) {
                  final state = ref.watch(chatProvider);
                  final transcript = state.liveTranscript;
                  final currentAmp = state.currentAmplitude;

                  // Interpolate the raw hardware decibels from (-60 to 0) into a (0.0 to 1.0) multiplier.
                  double ampNorm =
                      ((currentAmp + 60.0) / 60.0).clamp(0.05, 1.0);

                  return Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(24, (index) {
                      // Apply genuine hardware envelope scaled lightly with sin buffer to maintain smooth transitions.
                      double height = 4.0 +
                          (28.0 *
                              ampNorm *
                              (0.5 +
                                  0.5 *
                                      math.sin((val * 2 * math.pi) +
                                          (index * 0.4))));
                      return Container(
                          width: 3,
                          height: height,
                          margin: const EdgeInsets.symmetric(horizontal: 1.5),
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.6),
                            borderRadius: BorderRadius.circular(1.5),
                          ));
                    }),
                  );
                }),
              ),
              const SizedBox(width: 8),
              InkWell(
                onTap: () {
                  final p = ref.read(chatProvider.notifier);
                  if (ref.read(chatProvider).isListening) p.toggleListening();
                  if (ref.read(chatProvider).isVoiceTyping)
                    p.toggleVoiceTyping();
                },
                child: const Icon(Icons.close, color: Colors.white70, size: 18),
              ),
              const SizedBox(width: 16),
              InkWell(
                onTap: () {
                  final state = ref.read(chatProvider);
                  final p = ref.read(chatProvider.notifier);
                  if (state.liveTranscript.isNotEmpty) {
                    p.sendMessage(state.liveTranscript);
                  }
                  if (state.isListening) p.toggleListening();
                  if (state.isVoiceTyping) p.toggleVoiceTyping();
                },
                child: const Icon(Icons.check, color: Colors.white, size: 20),
              ),
              const SizedBox(width: 16),
            ],
          ),
        );
      },
    );
  }
}



class ChatView extends ConsumerStatefulWidget {
  const ChatView({super.key});

  @override
  ConsumerState<ChatView> createState() => _ChatViewState();
}

class _ChatViewState extends ConsumerState<ChatView> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  Future<List<dynamic>>? _dashboardFuture;

  @override
  void initState() {
    super.initState();
    _initLocation();
    _dashboardFuture = ref.read(apiClientProvider).fetchDashboardWidgets();
  }

  Future<void> _initLocation() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) return;
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) return;
    }
    Position pos = await Geolocator.getCurrentPosition();
    ref.read(apiClientProvider).setLocation(pos.latitude, pos.longitude);
  }

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
    final notifier = ref.read(chatProvider.notifier);
    notifier.sendMessage(val);
    notifier.setContinuousVoiceMode(false);
    _controller.clear();
    _scrollToBottom();
  }

  Future<void> _pickUnifiedFile() async {
    try {
      FilePickerResult? result = await FilePicker.pickFiles(withData: true);
      if (result != null && result.files.single.bytes != null) {
        final file = result.files.single;
        final ext = file.extension?.toLowerCase() ?? '';
        final isImage = ['png', 'jpg', 'jpeg', 'gif', 'webp'].contains(ext);
        
        final pendingFile = PendingFile(
          name: file.name,
          type: isImage ? 'image' : 'document',
          bytes: file.bytes!,
          base64Data: isImage ? base64Encode(file.bytes!) : "",
        );
        
        ref.read(chatProvider.notifier).attachFile(pendingFile);
      }
    } catch (e) {
      ref.read(chatProvider.notifier).addMessage("System: Attachment failed: $e");
    }
  }

  void _showEditTitleDialog(int id, String currentTitle) {
    final tc = TextEditingController(text: currentTitle);
    showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
              backgroundColor: const Color(0xFF1B1B1B),
              title: const Text('Edit Conversation Title',
                  style: TextStyle(color: Colors.white)),
              content: TextField(
                controller: tc,
                style: const TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  hintText: 'Enter new title',
                  hintStyle:
                      TextStyle(color: Colors.white.withValues(alpha: 0.4)),
                  enabledBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                          color: Colors.white.withValues(alpha: 0.1))),
                  focusedBorder: OutlineInputBorder(
                      borderSide: BorderSide(
                          color: Theme.of(context).colorScheme.primary)),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Cancel',
                      style: TextStyle(color: Colors.white54)),
                ),
                ElevatedButton(
                  onPressed: () {
                    if (tc.text.trim().isNotEmpty) {
                      ref
                          .read(chatProvider.notifier)
                          .updateChatTitle(id, tc.text.trim());
                    }
                    Navigator.pop(ctx);
                  },
                  style: ElevatedButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.primary),
                  child:
                      const Text('Save', style: TextStyle(color: Colors.white)),
                ),
              ],
            ));
  }

  Widget _buildDashboardWidgets() {
    final screenWidth = MediaQuery.of(context).size.width;
    int crossAxisCount = screenWidth > 1200 ? 3 : (screenWidth > 800 ? 2 : 1);

    return FutureBuilder<List<dynamic>>(
      future: _dashboardFuture,
      builder: (context, snapshot) {
        if (!snapshot.hasData || snapshot.data!.isEmpty) {
          return GridView.count(
            crossAxisCount: crossAxisCount,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            childAspectRatio:
                screenWidth > 800 ? 1.45 : 1.75, // Lower ratio = taller cards
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
          childAspectRatio:
              screenWidth > 800 ? 1.45 : 1.75, // Consistent aspect ratio
          children: List.generate(widgets.length, (index) {
            return _DashboardWidgetCard(
                data: widgets[index] as Map<String, dynamic>, index: index);
          }),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    // Autoscroll hooks
    ref.listen(chatProvider.select((state) => state.messages), (prev, next) {
      // If a new message was added, animate to bottom
      if (prev == null || prev.length != next.length) {
        _scrollToBottom();
      } else {
        // If streaming an existing message (or typewriter is running), smoothly track the bottom without animation spam
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (_scrollController.hasClients) {
            final pos = _scrollController.position;
            // Only force scroll if the user is near the bottom (allows scrolling up while generating)
            if (pos.maxScrollExtent - pos.pixels < 300) {
              _scrollController.jumpTo(pos.maxScrollExtent);
            }
          }
        });
      }
    });

    ref.listen(chatProvider.select((state) => state.streamingNodes), (prev, next) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          final pos = _scrollController.position;
          if (pos.maxScrollExtent - pos.pixels < 300) {
            _scrollController.jumpTo(pos.maxScrollExtent);
          }
        }
      });
    });
    
    ref.listen(chatProvider.select((state) => state.isProcessing), (prev, isProcessing) {
      // Scroll when processing starts (to show loading) AND when it ends (to snap to end of widget/message)
      _scrollToBottom();
    });
    
    // Removed explicit scroll on voice mode shrink to allow smooth general auto-scroll

    final isListening = ref.watch(chatProvider).isListening;
    final isVoiceTyping = ref.watch(chatProvider).isVoiceTyping;

    return Stack(
      children: [
        Column(
          children: [
            // Glassmorphism Header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              decoration: BoxDecoration(
                color: Theme.of(context)
                    .colorScheme
                    .surface
                    .withValues(alpha: 0.8),
                border: Border(
                    bottom: BorderSide(
                        color: Colors.white.withValues(alpha: 0.05))),
              ),
              child: Row(
                children: [
                  const Text('Workspace Overview',
                      style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w600,
                          letterSpacing: -0.5,
                          color: Colors.white)),
                  const Spacer(),
                  ElevatedButton.icon(
                    onPressed: () =>
                        ref.read(chatProvider.notifier).startNewChat(),
                    icon: const Icon(Icons.add_comment, size: 16),
                    label: const Text('New Chat'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Theme.of(context)
                          .colorScheme
                          .primary
                          .withValues(alpha: 0.15),
                      foregroundColor: Theme.of(context).colorScheme.primary,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 12),
                    ),
                  ),
                  const SizedBox(width: 16),
                  _buildHeaderAction(Icons.search, "Search"),

                  _buildHeaderAction(Icons.push_pin, "Pinned"),
                  const SizedBox(width: 16),
                  IconButton(
                      icon: const Icon(Icons.more_vert),
                      onPressed: () {},
                      color: Colors.white.withValues(alpha: 0.6)),
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
                  itemCount: chatState.messages.length +
                      1 +
                      (chatState.isProcessing ? 1 : 0) +
                      (chatState.pendingPlan != null ? 1 : 0),
                  itemBuilder: (context, index) {
                    if (index == 0) {
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 32.0),
                        child: _buildDashboardWidgets(),
                      );
                    }

                    // Loading indicator logic
                    if (chatState.isProcessing &&
                        index == chatState.messages.length + 1) {
                      return Center(
                        child: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 800),
                          child: Padding(
                            padding: const EdgeInsets.only(bottom: 24.0),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  margin: const EdgeInsets.only(right: 16),
                                  padding: const EdgeInsets.all(8),
                                  decoration: BoxDecoration(
                                    color: Theme.of(context)
                                        .colorScheme
                                        .primary
                                        .withValues(alpha: 0.15),
                                    shape: BoxShape.circle,
                                    border: Border.all(
                                        color: Theme.of(context)
                                            .colorScheme
                                            .primary
                                            .withValues(alpha: 0.3)),
                                  ),
                                  child: Icon(Icons.auto_awesome,
                                      color:
                                          Theme.of(context).colorScheme.primary,
                                      size: 20),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 20, vertical: 16),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF1B1B1B)
                                        .withValues(alpha: 0.9),
                                    borderRadius: const BorderRadius.only(
                                        topLeft: Radius.circular(24),
                                        topRight: Radius.circular(24),
                                        bottomLeft: Radius.circular(4),
                                        bottomRight: Radius.circular(24)),
                                    border: Border.all(
                                        color: Colors.white
                                            .withValues(alpha: 0.05)),
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Text(chatState.loadingText, style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 14)),
                                      const SizedBox(width: 8),
                                      const LoadingDots(),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    }

                    // Plan Approval Card
                    if (chatState.pendingPlan != null &&
                        index == chatState.messages.length + 1 + (chatState.isProcessing ? 1 : 0)) {
                      return _PlanApprovalCard(
                        plan: chatState.pendingPlan!,
                        onApprove: (steps) =>
                            ref.read(chatProvider.notifier).approvePlan(steps),
                        onCancel: () =>
                            ref.read(chatProvider.notifier).cancelPlan(),
                      );
                    }

                    final msg = chatState.messages[index - 1];
                    
                    if (msg.startsWith("System:")) {
                       return Center(
                         child: Padding(
                           padding: const EdgeInsets.symmetric(vertical: 24),
                           child: Column(
                             children: [
                               Container(height: 1, width: 120, color: Colors.white.withValues(alpha: 0.15)),
                               const SizedBox(height: 8),
                               Text(msg.replaceFirst("System:", "").trim().toUpperCase(), style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
                             ]
                           )
                         )
                       );
                    }

                    if (msg.startsWith("User: [AUTOMATED SCHEDULED TRIGGER]")) {
                       String dateStr = "";
                       String titleStr = "";
                       
                       final lines = msg.split('\n');
                       for (var line in lines) {
                           if (line.startsWith("Date: ")) {
                               dateStr = line.replaceFirst("Date: ", "").trim();
                           } else if (line.startsWith("Title: ")) {
                               titleStr = line.replaceFirst("Title: ", "").trim();
                           }
                       }
                       
                       return Center(
                         child: Padding(
                           padding: const EdgeInsets.symmetric(vertical: 24),
                           child: Column(
                             children: [
                               Container(height: 1, width: 120, color: Colors.white.withValues(alpha: 0.15)),
                               const SizedBox(height: 8),
                               Text("— ${titleStr.toUpperCase()} —", style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
                               if (dateStr.isNotEmpty) ...[
                                   const SizedBox(height: 4),
                                   Text(dateStr, style: TextStyle(color: Colors.white.withValues(alpha: 0.3), fontSize: 9)),
                               ]
                             ]
                           )
                         )
                       );
                    }

                    final isAssistant = msg.startsWith("Assistant:");
                    final displayMsg = isAssistant
                        ? msg.replaceFirst("Assistant:", "").trim()
                        : msg.replaceFirst("User:", "").trim();

                    // Only animate the very last assistant message if it just arrived
                    bool isLatestAssistant = isAssistant &&
                        (index - 1 == chatState.messages.length - 1) &&
                        !chatState.isSending;

                    // Clean text for the editor (without base64 blobs or document tags)
                    String cleanEditText = displayMsg;

                    // 1. Extract raw document tags for editor preservation
                    final List<String> rawAttachedDocs = [];
                    final documentRegexRaw = RegExp(r'\[Attached Document: .*? \(Uploaded to Memory\)\]\n?');
                    cleanEditText = cleanEditText.replaceAllMapped(documentRegexRaw, (match) {
                      rawAttachedDocs.add(match.group(0)!);
                      return '';
                    });

                    // 2. Extract raw image base64 tags for editor preservation
                    final List<String> rawAttachedImages = [];
                    final imageRegexRaw = RegExp(r'!\[attachment\]\(data:image\/[^;]+;base64,[^\)]+\)\n?');
                    cleanEditText = cleanEditText.replaceAllMapped(imageRegexRaw, (match) {
                      rawAttachedImages.add(match.group(0)!);
                      return '';
                    });
                    
                    cleanEditText = cleanEditText.trim();

                    // Extract markdown images to build collages natively
                    String processedMsg = displayMsg;
                    
                    // Parse attached documents
                    final List<String> attachedDocs = [];
                    final documentRegex = RegExp(r'\[Attached Document: (.*?) \(Uploaded to Memory\)\]\n?');
                    processedMsg = processedMsg.replaceAllMapped(documentRegex, (match) {
                      attachedDocs.add(match.group(1)!);
                      return '';
                    });

                    final List<String> sentImagesB64 = [];
                    if (!isAssistant) {
                      processedMsg = processedMsg.replaceAllMapped(imageRegexRaw, (match) {
                        String fullTag = match.group(0)!;
                        int idx = fullTag.indexOf('base64,');
                        if (idx != -1) {
                            String b64 = fullTag.substring(idx + 7, fullTag.indexOf(')'));
                            sentImagesB64.add(b64);
                        }
                        return '';
                      });
                    }
                    
                    final consecutiveImagesRegex = RegExp(r'(?:!\[.*?\]\(.*?\)\s*){2,}');
                    processedMsg = processedMsg.replaceAllMapped(consecutiveImagesRegex, (match) {
                      final block = match.group(0)!;
                      final urlRegex = RegExp(r'!\[.*?\]\((.*?)\)');
                      final urls = urlRegex.allMatches(block).map((m) => m.group(1)!).toList();
                      return '\n\n[COLLAGE:${urls.join('||')}]\n\n';
                    });

                    // Hide raw XML tool blocks from the UI
                    processedMsg = processedMsg.replaceAll(RegExp(r'<tool_call>[\s\S]*?(</tool_call>|$)', multiLine: true), '');
                    processedMsg = processedMsg.replaceAll(RegExp(r'<tool_response>[\s\S]*?(</tool_response>|$)', multiLine: true), '');
                    // Also clean up any loose <tool_call or </tool_call> that might have gotten split
                    processedMsg = processedMsg.replaceAll('<tool_call>', '').replaceAll('</tool_call>', '');
                    processedMsg = processedMsg.replaceAll('<tool_response>', '').replaceAll('</tool_response>', '');
                    
                    processedMsg = processedMsg.trim();

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
                      child: Center(
                        child: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 800),
                          child: Padding(
                            padding: const EdgeInsets.only(bottom: 24.0),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisAlignment: isAssistant
                                  ? MainAxisAlignment.start
                                  : MainAxisAlignment.end,
                              children: [
                                if (isAssistant)
                                  Container(
                                    margin: const EdgeInsets.only(right: 16),
                                    padding: const EdgeInsets.all(8),
                                    decoration: BoxDecoration(
                                      color: Theme.of(context)
                                          .colorScheme
                                          .primary
                                          .withValues(alpha: 0.15),
                                      shape: BoxShape.circle,
                                      border: Border.all(
                                          color: Theme.of(context)
                                              .colorScheme
                                              .primary
                                              .withValues(alpha: 0.3)),
                                    ),
                                    child: Icon(Icons.auto_awesome,
                                        color: Theme.of(context)
                                            .colorScheme
                                            .primary,
                                        size: 20),
                                  ),
                                Flexible(
                                  child: Builder(
                                    builder: (context) {
                                        Widget mdBody;
                                        // During streaming: use the live typed node list so each node
                                        // renders the moment it arrives rather than waiting for all nodes.
                                        // After stream ends: fall back to full-string parse for history rendering.
                                        final msgStateIndex = index - 1;
                                        final isThisMessageStreaming = isAssistant &&
                                            chatState.isSending &&
                                            msgStateIndex == chatState.messages.length - 1;
                                        final streamingKey = "${chatState.conversationId}_$msgStateIndex";
                                        final liveNodes = chatState.streamingNodes[streamingKey];
                                        final List<PresentationNode> parsedNodes;
                                        if (isAssistant) {
                                          if (isThisMessageStreaming && liveNodes != null && liveNodes.isNotEmpty) {
                                            // Live path — incremental render from state list
                                            parsedNodes = liveNodes
                                                .map((n) => PresentationNode.fromJson(n))
                                                .toList();
                                          } else {
                                            // History / fully loaded path — parse from accumulated string
                                            parsedNodes = StreamingParser.parseStream(processedMsg);
                                          }
                                        } else {
                                          parsedNodes = const [];
                                        }

                                        if (parsedNodes.isNotEmpty) {
                                            mdBody = PresentationRenderer(nodes: parsedNodes);
                                        } else {
                                            mdBody = AiMessageRenderer(
                                              text: processedMsg,
                                              isAssistant: isAssistant,
                                              isStreaming: isAssistant && chatState.isSending && index - 1 == chatState.messages.length - 1,
                                              inlineSyntaxes: [CollageSyntax()],
                                              builders: {'collage': CollageElementBuilder(context)},
                                          imageBuilder: (uri, title, alt) {
                                            final url = uri.toString();
                                            final lowerUrl = url.toLowerCase();
                                            if (lowerUrl.contains('wikimedia.org') || 
                                                lowerUrl.contains('wikipedia.org') || 
                                                lowerUrl.contains('unsplash.com')) {
                                              return const SizedBox.shrink();
                                            }
                                            
                                            final proxyUrl = '${ApiClient.baseUrl}/media/proxy?url=${Uri.encodeComponent(url)}';
                                            return GestureDetector(
                                              onTap: () {
                                                Navigator.of(context).push(
                                                  PageRouteBuilder(
                                                    opaque: false,
                                                    pageBuilder: (context, _, __) {
                                                      return _GalleryView(urls: [url], initialIndex: 0);
                                                    },
                                                  ),
                                                );
                                              },
                                              child: Container(
                                                margin: const EdgeInsets.symmetric(vertical: 8),
                                                constraints: const BoxConstraints(maxWidth: 400, maxHeight: 400),
                                                clipBehavior: Clip.antiAlias,
                                                decoration: BoxDecoration(
                                                  borderRadius: BorderRadius.circular(16),
                                                  border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
                                                  boxShadow: [
                                                    BoxShadow(
                                                      color: Colors.black.withValues(alpha: 0.2),
                                                      blurRadius: 10,
                                                      offset: const Offset(0, 4),
                                                    )
                                                  ]
                                                ),
                                                child: InteractiveViewer(
                                                  child: Image.network(
                                                    proxyUrl,
                                                    fit: BoxFit.contain,
                                                    headers: const {'Accept': 'image/*'},
                                                    errorBuilder: (context, error, stackTrace) => Image.network(
                                                      url,
                                                      errorBuilder: (context, error, stackTrace) {
                                                        return Container(
                                                          height: 120,
                                                          width: 120,
                                                          color: Colors.grey.withValues(alpha: 0.1),
                                                          child: const Center(
                                                            child: Icon(Icons.image_not_supported_outlined, color: Colors.white54, size: 32)
                                                          )
                                                        );
                                                      }
                                                    ),
                                                  ),
                                                ),
                                              ),
                                            );
                                          },
                                        );
                                        }
                                        
                                        List<Widget> attachments = [];
                                        if (!isAssistant) {
                                          for (var b64 in sentImagesB64) {
                                            attachments.add(_SentAttachmentPill(
                                              name: 'image', type: 'image', base64Data: b64, ext: 'png'
                                            ));
                                          }
                                        }
                                        for (var docName in attachedDocs) {
                                          String ext = docName.contains('.') ? docName.split('.').last.toLowerCase() : 'file';
                                          attachments.add(_SentAttachmentPill(
                                            name: docName, type: 'document', ext: ext
                                          ));
                                        }
                                        
                                        if (attachments.isNotEmpty) {
                                          Widget attachWidget = Wrap(
                                            spacing: 8,
                                            runSpacing: 8,
                                            children: attachments,
                                          );
                                          
                                          if (processedMsg.isEmpty) {
                                            mdBody = attachWidget;
                                          } else {
                                            mdBody = Column(
                                              crossAxisAlignment: isAssistant ? CrossAxisAlignment.start : CrossAxisAlignment.end,
                                              children: [
                                                attachWidget,
                                                const SizedBox(height: 12),
                                                mdBody,
                                              ],
                                            );
                                          }
                                        }

                                        if (!isAssistant) {
                                          return _UserMessageEditor(
                                            initialText: cleanEditText,
                                            markdownBody: mdBody,
                                            onSave: (newText) {
                                              String finalMsg = newText.trim();
                                              for (var doc in rawAttachedDocs) {
                                                if (!finalMsg.contains(doc.trim())) {
                                                  finalMsg += '\n${doc.trim()}';
                                                }
                                              }
                                              for (var img in rawAttachedImages) {
                                                if (!finalMsg.contains(img.trim())) {
                                                  finalMsg += '\n${img.trim()}';
                                                }
                                              }
                                              ref.read(chatProvider.notifier).editMessageAndSend(index - 1, finalMsg);
                                            },
                                            onCopy: () {
                                              Clipboard.setData(ClipboardData(text: cleanEditText));
                                            },
                                          );
                                        }

                                        return Container(
                                          padding: const EdgeInsets.only(top: 8, bottom: 8),
                                          child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                                mdBody,
                                              
                                          if (chatState.messageMetadata[
                                                      index - 1] !=
                                                  null) ...[
                                            if (chatState.messageMetadata[
                                                        index - 1]![
                                                    'requires_confirmation'] ==
                                                true)
                                              _PlanApprovalRequestPanel(
                                                  metadata:
                                                      chatState.messageMetadata[
                                                          index - 1]!),
                                            _ExplainabilityPanel(
                                                metadata: chatState
                                                    .messageMetadata[index - 1]),
                                          ],
                                          const SizedBox(height: 12),
                                          Row(
                                            mainAxisSize: MainAxisSize.min,
                                            children: [
                                              InkWell(
                                                onTap: () {
                                                  Clipboard.setData(ClipboardData(
                                                      text: displayMsg));
                                                },
                                                child: Icon(Icons.copy_outlined,
                                                    size: 16,
                                                    color: Colors.white
                                                        .withValues(alpha: 0.5)),
                                              ),
                                                const SizedBox(width: 16),
                                                InkWell(
                                                  onTap: () => ref
                                                      .read(chatProvider.notifier)
                                                      .readAloud(displayMsg),
                                                  child: Icon(
                                                      Icons.volume_up_outlined,
                                                      size: 16,
                                                      color: Colors.white
                                                          .withValues(
                                                              alpha: 0.5)),
                                                ),
                                                const SizedBox(width: 16),
                                                InkWell(
                                                  onTap: () {},
                                                  child: Icon(
                                                      Icons.thumb_up_outlined,
                                                      size: 16,
                                                      color: Colors.white
                                                          .withValues(
                                                              alpha: 0.5)),
                                                ),
                                                const SizedBox(width: 16),
                                                InkWell(
                                                  onTap: () {},
                                                  child: Icon(
                                                      Icons.thumb_down_outlined,
                                                      size: 16,
                                                      color: Colors.white
                                                          .withValues(
                                                              alpha: 0.5)),
                                                ),
                                                const SizedBox(width: 16),
                                                InkWell(
                                                  onTap: () => ref
                                                      .read(chatProvider.notifier)
                                                      .regenerateLastResponse(),
                                                  child: Icon(Icons.refresh,
                                                      size: 16,
                                                      color: Colors.white
                                                          .withValues(
                                                              alpha: 0.5)),
                                                ),
                                            ],
                                          )
                                        ],
                                          ),
                                        );
                                      }
                                    ),
                                  ),
                                if (!isAssistant)
                                  Container(
                                    margin: const EdgeInsets.only(left: 16),
                                    padding: const EdgeInsets.all(8),
                                    decoration: BoxDecoration(
                                      color:
                                          Colors.white.withValues(alpha: 0.1),
                                      shape: BoxShape.circle,
                                      border: Border.all(
                                          color: Colors.white
                                              .withValues(alpha: 0.1)),
                                    ),
                                    child: Icon(Icons.person,
                                        color:
                                            Colors.white.withValues(alpha: 0.8),
                                        size: 20),
                                  ),
                              ],
                            ),
                          ),
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
              final isProcessing = ref.watch(chatProvider).isProcessing;
              final isEmpty = ref.watch(chatProvider).messages.isEmpty;
              final isContinuousVoiceMode = ref.watch(chatProvider).isContinuousVoiceMode;

              return Positioned.fill(
                child: Container(
                padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
                color: Colors.transparent,
                child: SafeArea(
                  child: AnimatedAlign(
                    duration: const Duration(milliseconds: 600),
                    curve: Curves.easeOutCubic,
                    alignment: isEmpty
                        ? const Alignment(0, 0.3)
                        : Alignment.bottomCenter,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                          AnimatedSize(
                            duration: const Duration(milliseconds: 600),
                            curve: Curves.easeOutCubic,
                            child: SizedBox(
                              height: isEmpty ? null : 0,
                              child: AnimatedOpacity(
                                duration: const Duration(milliseconds: 400),
                                opacity: isEmpty ? 1.0 : 0.0,
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                          const Text("Greetings, Ayush",
                              style: TextStyle(
                                  fontSize: 32,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white,
                                  letterSpacing: -0.5)),
                          const SizedBox(height: 12),
                          Text("What's on your mind today?",
                              style: TextStyle(
                                  fontSize: 18,
                                  color: Colors.white.withValues(alpha: 0.6))),
                          const SizedBox(height: 48),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ChatInputPill(controller: _controller, onSend: () => _handleSend(_controller.text)),
                      ], // End Column children
                    ), // End Column
                  ), // End AnimatedAlign
                ), // End SafeArea
              )); // End return Positioned.fill
            }), // End Consumer
          ], // End main Column children
        ), // End main Column
        
        // Voice session overlay
        const VoiceModeView(),
      ], // End Stack children
    ); // End Stack
  }

  Widget _buildHeaderAction(IconData icon, String label,
      {bool active = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          Icon(icon,
              size: 18,
              color: active
                  ? Theme.of(context).colorScheme.primary
                  : Colors.white.withValues(alpha: 0.6)),
          const SizedBox(width: 8),
          Text(label,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: active
                    ? Theme.of(context).colorScheme.primary
                    : Colors.white.withValues(alpha: 0.6),
              )),
        ],
      ),
    );
  }

  Widget _buildHeaderDivider() {
    return Container(
      height: 16,
      width: 1,
      color: Colors.white.withValues(alpha: 0.1),
    );
  }
}

class _PlanApprovalRequestPanel extends StatelessWidget {
  final Map<String, dynamic> metadata;
  const _PlanApprovalRequestPanel({required this.metadata});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 16, bottom: 8),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.4),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.orangeAccent.withValues(alpha: 0.3)),
        boxShadow: [
          BoxShadow(
              color: Colors.orangeAccent.withValues(alpha: 0.05),
              blurRadius: 20)
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.warning_amber_rounded,
                  color: Colors.orangeAccent, size: 20),
              SizedBox(width: 8),
              Text('Approval Required',
                  style: TextStyle(
                      color: Colors.orangeAccent,
                      fontWeight: FontWeight.bold,
                      fontSize: 14)),
            ],
          ),
          const SizedBox(height: 12),
          Text(metadata['pending_tool_name'] ?? 'Agent Plan Execution',
              style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  color: Colors.white,
                  fontSize: 16)),
          const SizedBox(height: 4),
          Text(
              'The agent requires confirmation before proceeding with this action natively.',
              style: TextStyle(
                  fontSize: 13, color: Colors.white.withValues(alpha: 0.6))),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton(
                onPressed: () {},
                child: const Text('Reject',
                    style: TextStyle(color: Colors.redAccent)),
              ),
              const SizedBox(width: 12),
              ElevatedButton.icon(
                onPressed: () {},
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orangeAccent,
                  foregroundColor: Colors.black,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8)),
                ),
                icon: const Icon(Icons.check, size: 16),
                label: const Text('EXECUTE PLAN'),
              ),
            ],
          )
        ],
      ),
    );
  }
}

class _ExplainabilityPanel extends StatefulWidget {
  final Map<String, dynamic>? metadata;
  const _ExplainabilityPanel({this.metadata});

  @override
  State<_ExplainabilityPanel> createState() => _ExplainabilityPanelState();
}

class _ExplainabilityPanelState extends State<_ExplainabilityPanel> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    if (widget.metadata == null) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 12),
        InkWell(
          onTap: () => setState(() => _expanded = !_expanded),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.info_outline,
                  size: 14, color: Colors.blueAccent.withValues(alpha: 0.8)),
              const SizedBox(width: 6),
              Text("Why did you say that?",
                  style: TextStyle(
                      color: Colors.blueAccent.withValues(alpha: 0.8),
                      fontSize: 12)),
            ],
          ),
        ),
        if (_expanded)
          Container(
            margin: const EdgeInsets.only(top: 12),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildMetaRow(
                    "Model / Routing",
                    widget.metadata!['model_used']?.toString() ??
                        "Provider API"),
                const SizedBox(height: 4),
                _buildMetaRow("Retrieved Sources",
                    "${widget.metadata!['retrieval_chunks'] ?? 0} contextual chunks"),
                const SizedBox(height: 4),
                _buildMetaRow("Execution Latency",
                    "${widget.metadata!['latency_ms'] ?? 0} ms"),
                if (widget.metadata!['memories'] != null &&
                    (widget.metadata!['memories'] as List).isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text("Memories Used:",
                      style: TextStyle(
                          color: Colors.white.withValues(alpha: 0.5), fontSize: 11)),
                  const SizedBox(height: 4),
                  ...(widget.metadata!['memories'] as List).map((m) =>
                      Padding(
                        padding: const EdgeInsets.only(bottom: 2),
                        child: Text(m.toString(),
                            style: TextStyle(
                                color: Colors.white.withValues(alpha: 0.9),
                                fontSize: 11,
                                fontStyle: FontStyle.italic)),
                      )),
                ]
              ],
            ),
          )
      ],
    );
  }

  Widget _buildMetaRow(String label, String value) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text("$label: ",
            style: TextStyle(
                color: Colors.white.withValues(alpha: 0.5), fontSize: 11)),
        Text(value,
            style: TextStyle(
                color: Colors.white.withValues(alpha: 0.9),
                fontSize: 11,
                fontFamily: 'monospace')),
      ],
    );
  }
}

class _SkeletonDashboardCard extends StatefulWidget {
  const _SkeletonDashboardCard();

  @override
  State<_SkeletonDashboardCard> createState() => _SkeletonDashboardCardState();
}

class _SkeletonDashboardCardState extends State<_SkeletonDashboardCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 1400))
      ..repeat(reverse: true);
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
        final baseColor = Colors.white.withValues(alpha: opacity);
        return ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 16.0, sigmaY: 16.0),
            child: Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.04),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
                boxShadow: [
                  BoxShadow(
                      color: Colors.black.withValues(alpha: 0.2),
                      blurRadius: 40,
                      spreadRadius: -10)
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                              color: baseColor, shape: BoxShape.circle)),
                      Container(
                          width: 72,
                          height: 24,
                          decoration: BoxDecoration(
                              color: baseColor,
                              borderRadius: BorderRadius.circular(12))),
                    ],
                  ),
                  const SizedBox(height: 20),
                  Container(
                      width: 140,
                      height: 26,
                      decoration: BoxDecoration(
                          color: baseColor,
                          borderRadius: BorderRadius.circular(8))),
                  const SizedBox(height: 12),
                  Container(
                      width: double.infinity,
                      height: 12,
                      decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: opacity * 0.7),
                          borderRadius: BorderRadius.circular(4))),
                  const SizedBox(height: 8),
                  Container(
                      width: 180,
                      height: 12,
                      decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: opacity * 0.7),
                          borderRadius: BorderRadius.circular(4))),
                  const SizedBox(height: 16),
                  Expanded(
                    child: Container(
                        width: double.infinity,
                        decoration: BoxDecoration(
                            color:
                                Colors.white.withValues(alpha: opacity * 0.5),
                            borderRadius: BorderRadius.circular(16))),
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
  final String condition;
  final double size;
  const AnimatedWeatherIcon({super.key, required this.condition, this.size = 48});
  @override
  State<AnimatedWeatherIcon> createState() => _AnimatedWeatherIconState();
}

class _AnimatedWeatherIconState extends State<AnimatedWeatherIcon>
    with TickerProviderStateMixin {
  late final AnimationController _pulseCtrl;
  late final AnimationController _spinCtrl;
  late final AnimationController _driftCtrl;
  late final AnimationController _rainCtrl;
  
  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(vsync: this, duration: const Duration(seconds: 2))..repeat(reverse: true);
    _spinCtrl = AnimationController(vsync: this, duration: const Duration(seconds: 15))..repeat();
    _driftCtrl = AnimationController(vsync: this, duration: const Duration(seconds: 4))..repeat(reverse: true);
    _rainCtrl = AnimationController(vsync: this, duration: const Duration(seconds: 1))..repeat();
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    _spinCtrl.dispose();
    _driftCtrl.dispose();
    _rainCtrl.dispose();
    super.dispose();
  }

  Widget _buildSun() {
    return AnimatedBuilder(
      animation: Listenable.merge([_spinCtrl, _pulseCtrl]),
      builder: (ctx, _) => Transform.scale(
        scale: 0.95 + (_pulseCtrl.value * 0.05),
        child: Transform.rotate(
          angle: _spinCtrl.value * 2 * 3.14159,
          child: Icon(Icons.wb_sunny, size: widget.size, color: Colors.orangeAccent),
        ),
      ),
    );
  }

  Widget _buildMoon() {
    return AnimatedBuilder(
      animation: _pulseCtrl,
      builder: (ctx, _) => Stack(
        children: [
          Positioned(
            top: widget.size * 0.1, right: widget.size * 0.1,
            child: Icon(Icons.nights_stay, size: widget.size * 0.8, color: Colors.blueAccent.shade100),
          ),
          Positioned(
            top: widget.size * 0.05, left: widget.size * 0.1,
            child: Opacity(opacity: _pulseCtrl.value, child: Icon(Icons.star, size: widget.size * 0.3, color: Colors.yellowAccent)),
          ),
          Positioned(
            left: widget.size * 0.5, bottom: widget.size * 0.15,
            child: Opacity(opacity: 1.0 - _pulseCtrl.value, child: Icon(Icons.star, size: widget.size * 0.2, color: Colors.yellowAccent)),
          ),
        ],
      ),
    );
  }

  Widget _buildCloud({Color color = Colors.white70}) {
    return AnimatedBuilder(
      animation: _driftCtrl,
      builder: (ctx, _) => Transform.translate(
        offset: Offset((_driftCtrl.value - 0.5) * widget.size * 0.15, 0),
        child: Icon(Icons.cloud, size: widget.size, color: color),
      ),
    );
  }

  Widget _buildRain() {
    return Stack(
      children: [
        _buildCloud(color: Colors.white54),
        Positioned.fill(
          child: AnimatedBuilder(
            animation: _rainCtrl,
            builder: (ctx, _) => CustomPaint(
              painter: _RainPainter(progress: _rainCtrl.value, color: Colors.lightBlueAccent, density: 4),
            ),
          ),
        )
      ],
    );
  }

  Widget _buildFog() {
    return Stack(
      children: [
        _buildCloud(color: Colors.white24),
        AnimatedBuilder(
          animation: _pulseCtrl,
          builder: (ctx, _) => Opacity(
            opacity: 0.5 + (_pulseCtrl.value * 0.3),
            child: Icon(Icons.dehaze, size: widget.size, color: Colors.white54),
          ),
        )
      ],
    );
  }

  Widget _buildPartlyCloudy() {
    return Stack(
      children: [
        Positioned(
          top: 0, right: 0,
          child: AnimatedBuilder(
            animation: _spinCtrl,
            builder: (ctx, _) => Transform.rotate(
              angle: _spinCtrl.value * 2 * 3.14159,
              child: Icon(Icons.wb_sunny, size: widget.size * 0.6, color: Colors.orangeAccent),
            ),
          ),
        ),
        Positioned(
            bottom: widget.size * 0.05, left: widget.size * 0.05,
            child: AnimatedBuilder(
              animation: _driftCtrl,
              builder: (ctx, _) => Transform.translate(
                offset: Offset((_driftCtrl.value - 0.5) * widget.size * 0.15, 0),
                child: Icon(Icons.cloud, size: widget.size * 0.75, color: Colors.white70),
              ),
            ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final c = widget.condition.toLowerCase();
    
    if (c.contains('rain') || c.contains('storm') || c.contains('drizzle') || c.contains('shower')) {
      return SizedBox(width: widget.size, height: widget.size, child: _buildRain());
    } else if (c.contains('fog') || c.contains('mist') || c.contains('haze')) {
      return SizedBox(width: widget.size, height: widget.size, child: _buildFog());
    } else if (c.contains('night') || c.contains('moon')) {
      return SizedBox(width: widget.size, height: widget.size, child: _buildMoon());
    } else if (c.contains('partly') || c.contains('few') || (c.contains('sun') && c.contains('cloud'))) {
      return SizedBox(width: widget.size, height: widget.size, child: _buildPartlyCloudy());
    } else if (c.contains('cloud') || c.contains('overcast')) {
      return SizedBox(width: widget.size, height: widget.size, child: _buildCloud());
    } else if (c.contains('sun') || c.contains('clear')) {
      return SizedBox(width: widget.size, height: widget.size, child: _buildSun());
    }
    
    // Default fallback
    return SizedBox(width: widget.size, height: widget.size, child: _buildPartlyCloudy());
  }
}

class _RainPainter extends CustomPainter {
  final double progress;
  final Color color;
  final int density;
  
  _RainPainter({required this.progress, required this.color, required this.density});
  
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = color
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;
      
    final w = size.width;
    final h = size.height;
    
    for (int i = 0; i < density; i++) {
      final offset = (i / density);
      final yProgress = (progress + offset) % 1.0;
      
      final x = w * (0.2 + (0.6 * (i / (density - 1))));
      final y = h * 0.4 + (h * 0.6 * yProgress); 
      
      canvas.drawLine(Offset(x, y), Offset(x, y + (h * 0.15)), p);
    }
  }

  @override
  bool shouldRepaint(covariant _RainPainter oldDelegate) => true;
}

class _DashboardWidgetCard extends StatefulWidget {
  final Map<String, dynamic> data;
  final int index;
  const _DashboardWidgetCard({required this.data, required this.index});
  @override
  State<_DashboardWidgetCard> createState() => _DashboardWidgetCardState();
}

class _DashboardWidgetCardState extends State<_DashboardWidgetCard>
    with AutomaticKeepAliveClientMixin {
  bool _isHovered = false;
  late PageController _pageController;

  @override
  bool get wantKeepAlive => true;

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

  IconData _getStaticWeatherIcon(String condition) {
    final c = condition.toLowerCase();
    if (c.contains('storm') || c.contains('thunder')) return Icons.thunderstorm;
    if (c.contains('rain') || c.contains('drizzle') || c.contains('shower')) return Icons.water_drop;
    if (c.contains('snow')) return Icons.ac_unit;
    if (c.contains('fog') || c.contains('mist') || c.contains('haze')) return Icons.foggy;
    if (c.contains('night') || c.contains('moon')) return Icons.nights_stay;
    if (c.contains('partly') || c.contains('few') || (c.contains('sun') && c.contains('cloud'))) return Icons.cloud_queue;
    if (c.contains('cloud') || c.contains('overcast')) return Icons.cloud;
    return Icons.wb_sunny;
  }

  Widget _buildWeatherInner() {
    final w = widget.data;
    final forecast = w['forecast'] as List<dynamic>? ?? [];
    final displayCond = w['condition']?.toString() ?? w['subtitle']?.toString() ?? 'Sunny';
    
    String iconCond = displayCond;
    if (w['is_day'] == 0) {
      iconCond += " night";
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Text(w['title'] ?? '',
                    style: const TextStyle(
                        fontSize: 48,
                        fontWeight: FontWeight.w400,
                        color: Colors.white,
                        letterSpacing: -1.0,
                        height: 1.0)),
                const SizedBox(width: 12),
                AnimatedWeatherIcon(condition: iconCond, size: 42),
              ]
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(displayCond,
                    style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: Colors.white)),
                const SizedBox(height: 4),
                Text('Feels like ${(double.tryParse((w['title'] ?? '0').replaceAll('°C', '')) ?? 0) + 2}°',
                    style: TextStyle(
                        fontSize: 12,
                        color: Colors.white.withValues(alpha: 0.5))),
              ],
            ),
          ],
        ),
        if (w['ai_summary'] != null && w['ai_summary'].toString().isNotEmpty) ...[
          const SizedBox(height: 16),
          Expanded(
            child: Text(w['ai_summary'] ?? '',
                style: TextStyle(
                    fontSize: 13,
                    height: 1.4,
                    color: Colors.white.withValues(alpha: 0.8)),
                maxLines: 3,
                overflow: TextOverflow.ellipsis),
          ),
        ] else
          const Spacer(),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: forecast.map((f) {
            return Column(
              children: [
                Text(f['day'].toString(),
                    style: TextStyle(
                        fontSize: 11,
                        color: Colors.white.withValues(alpha: 0.5))),
                const SizedBox(height: 6),
                Icon(_getStaticWeatherIcon(f['condition']?.toString() ?? ''),
                    size: 20, color: Colors.white.withValues(alpha: 0.85)),
                const SizedBox(height: 6),
                Text("${f['high']}°",
                    style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                        color: Colors.white)),
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
                Text(w['title'] ?? '',
                    style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.white)),
                Text(w['badge'] ?? '',
                    style: TextStyle(
                        fontSize: 12,
                        color: Colors.white.withValues(alpha: 0.5))),
              ],
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                  color: Colors.indigoAccent.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(12)),
              child: const Text('Today',
                  style: TextStyle(
                      color: Colors.indigoAccent,
                      fontSize: 11,
                      fontWeight: FontWeight.bold)),
            )
          ],
        ),
        if (w['ai_summary'] != null &&
            w['ai_summary'].toString().isNotEmpty) ...[
          const SizedBox(height: 12),
          Text(w['ai_summary'] ?? '',
              style: TextStyle(
                  fontSize: 13,
                  height: 1.4,
                  color: Colors.white.withValues(alpha: 0.8)),
              maxLines: 2,
              overflow: TextOverflow.ellipsis),
        ],
        const SizedBox(height: 12),
        Expanded(
          child: LayoutBuilder(builder: (context, constraints) {
            int rows = (grid.length / 7).ceil();
            if (rows == 0) rows = 1;
            double itemWidth = constraints.maxWidth / 7;
            double itemHeight = constraints.maxHeight / rows;
            double safeRatio = (itemWidth > 0 && itemHeight > 0)
                ? (itemWidth / itemHeight)
                : 1.0;

            return GridView.builder(
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 7,
                  childAspectRatio: safeRatio,
                  mainAxisSpacing: 4,
                  crossAxisSpacing: 4),
              itemCount: grid.length,
              itemBuilder: (context, idx) {
                final d = grid[idx];
                if (d['day'] == 0) return const SizedBox();
                bool isEvent = d['hasEvent'] ?? false;
                bool isToday = d['day'] == w['current_day'];
                return Container(
                  decoration: BoxDecoration(
                    color: isToday
                        ? Colors.indigoAccent
                        : (isEvent
                            ? Colors.white.withValues(alpha: 0.08)
                            : Colors.transparent),
                    shape: BoxShape.circle,
                  ),
                  alignment: Alignment.center,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Flexible(
                          child: Text(d['day'].toString(),
                              style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: isToday
                                      ? FontWeight.bold
                                      : FontWeight.normal,
                                  color: Colors.white.withValues(
                                      alpha: isToday ? 1.0 : 0.6)))),
                      if (isEvent && !isToday)
                        Container(
                            margin: const EdgeInsets.only(top: 2),
                            width: 4,
                            height: 4,
                            decoration: const BoxDecoration(
                                color: Colors.indigoAccent,
                                shape: BoxShape.circle)),
                    ],
                  ),
                );
              },
            );
          }),
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
                          const Text("Top News",
                              style: TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.white)),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                                color: Colors.green.withValues(alpha: 0.2),
                                borderRadius: BorderRadius.circular(12)),
                            child: Text(
                                article['domain'].toString().toUpperCase(),
                                style: const TextStyle(
                                    color: Colors.greenAccent,
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold)),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(article['title'] ?? '',
                          style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                              height: 1.2),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis),
                      const SizedBox(height: 12),
                      Expanded(
                        child: Text(article['summary'] ?? '',
                            style: TextStyle(
                                fontSize: 13,
                                height: 1.6,
                                color: Colors.white.withValues(alpha: 0.6)),
                            overflow: TextOverflow.fade),
                      ),
                      const SizedBox(
                          height: 24), // Avoid crossing over the arrow bounds
                    ],
                  ),
                );
              },
            ),
            Positioned(
                bottom: 0,
                right: 0,
                child: Row(
                  children: [
                    IconButton(
                        icon: Icon(Icons.chevron_left,
                            color: Colors.white.withValues(alpha: 0.5)),
                        onPressed: () {
                          _pageController.previousPage(
                              duration: const Duration(milliseconds: 300),
                              curve: Curves.ease);
                        }),
                    IconButton(
                        icon: Icon(Icons.chevron_right,
                            color: Colors.white.withValues(alpha: 0.5)),
                        onPressed: () {
                          _pageController.nextPage(
                              duration: const Duration(milliseconds: 300),
                              curve: Curves.ease);
                        }),
                  ],
                ))
          ],
        ))
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
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
                          color:
                              const Color(0xFF1F1F1F).withValues(alpha: 0.35),
                          borderRadius: BorderRadius.circular(32),
                          border: Border.all(
                              color: Colors.white
                                  .withValues(alpha: _isHovered ? 0.15 : 0.05)),
                          boxShadow: [
                            BoxShadow(
                                color: Colors.black
                                    .withValues(alpha: _isHovered ? 0.3 : 0.1),
                                blurRadius: _isHovered ? 24 : 10,
                                offset: Offset(0, _isHovered ? 8 : 4))
                          ],
                        ),
                        child: id == 'weather'
                            ? _buildWeatherInner()
                            : id == 'calendar'
                                ? _buildCalendarInner()
                                : id == 'news'
                                    ? _buildNewsInner()
                                    : const SizedBox(),
                      ),
                    ),
                  ),
                ),
              ),
            ),
          );
    });
  }
}

class WaveformCircleIcon extends StatelessWidget {
  const WaveformCircleIcon({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(color: Colors.white.withValues(alpha: 0.2), blurRadius: 8)
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(width: 2.5, height: 10, decoration: BoxDecoration(color: Colors.black, borderRadius: BorderRadius.circular(2))),
          const SizedBox(width: 2.5),
          Container(width: 2.5, height: 18, decoration: BoxDecoration(color: Colors.black, borderRadius: BorderRadius.circular(2))),
          const SizedBox(width: 2.5),
          Container(width: 2.5, height: 14, decoration: BoxDecoration(color: Colors.black, borderRadius: BorderRadius.circular(2))),
          const SizedBox(width: 2.5),
          Container(width: 2.5, height: 8, decoration: BoxDecoration(color: Colors.black, borderRadius: BorderRadius.circular(2))),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// PLAN APPROVAL CARD
// ─────────────────────────────────────────────────────────────────────────────
class _PlanApprovalCard extends StatefulWidget {
  final List<Map<String, dynamic>> plan;
  final void Function(List<Map<String, dynamic>> approvedSteps) onApprove;
  final VoidCallback onCancel;

  const _PlanApprovalCard({
    required this.plan,
    required this.onApprove,
    required this.onCancel,
  });

  @override
  State<_PlanApprovalCard> createState() => _PlanApprovalCardState();
}

class _PlanApprovalCardState extends State<_PlanApprovalCard>
    with SingleTickerProviderStateMixin {
  late List<Map<String, dynamic>> _steps;
  late List<bool> _enabled;
  bool _editMode = false;
  late AnimationController _anim;
  late Animation<double> _fadeAnim;

  static const Map<String, IconData> _toolIcons = {
    'browser_automation': Icons.public,
    'web_search': Icons.search,
    'google_calendar': Icons.calendar_today,
    'gmail': Icons.mail_outline,
    'google_drive': Icons.drive_file_move_outline,
    'create_note': Icons.note_add_outlined,
    'document_search': Icons.manage_search,
    'memory_search': Icons.psychology_outlined,
    'tasks': Icons.task_alt,
    'reminders_tool': Icons.alarm,
    'computer_control': Icons.computer,
  };

  @override
  void initState() {
    super.initState();
    _steps = List.from(widget.plan);
    _enabled = List.filled(widget.plan.length, true);
    _anim = AnimationController(vsync: this, duration: const Duration(milliseconds: 400));
    _fadeAnim = CurvedAnimation(parent: _anim, curve: Curves.easeOutCubic);
    _anim.forward();
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  IconData _iconFor(String toolName) =>
      _toolIcons.entries.firstWhere(
        (e) => toolName.contains(e.key),
        orElse: () => MapEntry('', Icons.build_outlined),
      ).value;

  String _formatArgs(Map args) {
    if (args.isEmpty) return '';
    final entries = args.entries.take(2).map((e) {
      final val = e.value?.toString() ?? '';
      return '${e.key}: ${val.length > 30 ? "${val.substring(0, 30)}…" : val}';
    });
    return '(${entries.join(', ')})';
  }

  @override
  Widget build(BuildContext context) {
    final approvedSteps = [
      for (int i = 0; i < _steps.length; i++)
        if (_enabled[i]) _steps[i],
    ];

    return FadeTransition(
      opacity: _fadeAnim,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 800),
          child: Padding(
            padding: const EdgeInsets.only(bottom: 24.0),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  margin: const EdgeInsets.only(right: 16),
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFB300).withValues(alpha: 0.15),
                    shape: BoxShape.circle,
                    border: Border.all(color: const Color(0xFFFFB300).withValues(alpha: 0.4)),
                  ),
                  child: const Icon(Icons.schema_outlined, color: Color(0xFFFFB300), size: 20),
                ),
                Flexible(
                  child: Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFF1A1A1A),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: const Color(0xFFFFB300).withValues(alpha: 0.25)),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFFFFB300).withValues(alpha: 0.06),
                          blurRadius: 20,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Header
                        Padding(
                          padding: const EdgeInsets.fromLTRB(20, 16, 16, 12),
                          child: Row(
                            children: [
                              const Icon(Icons.pending_actions_outlined,
                                  size: 16, color: Color(0xFFFFB300)),
                              const SizedBox(width: 8),
                              const Text(
                                'Action Plan — Review Required',
                                style: TextStyle(
                                  color: Color(0xFFFFB300),
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                  letterSpacing: 0.3,
                                ),
                              ),
                              const Spacer(),
                              GestureDetector(
                                onTap: () => setState(() => _editMode = !_editMode),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: _editMode
                                        ? Colors.white.withValues(alpha: 0.08)
                                        : Colors.transparent,
                                    borderRadius: BorderRadius.circular(8),
                                    border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
                                  ),
                                  child: Text(
                                    _editMode ? 'Done Editing' : 'Edit',
                                    style: TextStyle(
                                      color: Colors.white.withValues(alpha: 0.6),
                                      fontSize: 11,
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),

                        // Divider
                        Divider(color: Colors.white.withValues(alpha: 0.06), height: 1),

                        // Steps
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          child: Column(
                            children: List.generate(_steps.length, (i) {
                              final step = _steps[i];
                              final args = (step['arguments'] as Map?) ?? {};
                              final icon = _iconFor(step['name']?.toString() ?? '');
                              final isEnabled = _enabled[i];

                              return AnimatedOpacity(
                                duration: const Duration(milliseconds: 200),
                                opacity: isEnabled ? 1.0 : 0.4,
                                child: Container(
                                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                                  decoration: BoxDecoration(
                                    color: Colors.white.withValues(alpha: isEnabled ? 0.03 : 0.01),
                                    borderRadius: BorderRadius.circular(10),
                                    border: Border.all(
                                      color: Colors.white.withValues(alpha: isEnabled ? 0.08 : 0.04),
                                    ),
                                  ),
                                  child: Row(
                                    children: [
                                      Container(
                                        width: 22,
                                        height: 22,
                                        decoration: BoxDecoration(
                                          color: Colors.white.withValues(alpha: 0.05),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        alignment: Alignment.center,
                                        child: Text(
                                          '${i + 1}',
                                          style: TextStyle(
                                            color: Colors.white.withValues(alpha: 0.5),
                                            fontSize: 10,
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ),
                                      const SizedBox(width: 10),
                                      Icon(icon, size: 14, color: Colors.white.withValues(alpha: 0.5)),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: RichText(
                                          text: TextSpan(
                                            children: [
                                              TextSpan(
                                                text: step['name']?.toString() ?? 'unknown',
                                                style: const TextStyle(
                                                  color: Colors.white,
                                                  fontSize: 12,
                                                  fontWeight: FontWeight.w500,
                                                  fontFamily: 'monospace',
                                                ),
                                              ),
                                              TextSpan(
                                                text: ' ${_formatArgs(args)}',
                                                style: TextStyle(
                                                  color: Colors.white.withValues(alpha: 0.4),
                                                  fontSize: 11,
                                                  fontFamily: 'monospace',
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                      ),
                                      if (_editMode)
                                        GestureDetector(
                                          onTap: () => setState(() => _enabled[i] = !_enabled[i]),
                                          child: Icon(
                                            isEnabled ? Icons.remove_circle_outline : Icons.add_circle_outline,
                                            size: 18,
                                            color: isEnabled
                                                ? Colors.redAccent.withValues(alpha: 0.7)
                                                : Colors.greenAccent.withValues(alpha: 0.7),
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                              );
                            }),
                          ),
                        ),

                        Divider(color: Colors.white.withValues(alpha: 0.06), height: 1),

                        // Action buttons
                        Padding(
                          padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
                          child: Row(
                            children: [
                              Text(
                                '${approvedSteps.length} of ${_steps.length} steps selected',
                                style: TextStyle(
                                  color: Colors.white.withValues(alpha: 0.35),
                                  fontSize: 11,
                                ),
                              ),
                              const Spacer(),
                              // Cancel
                              GestureDetector(
                                onTap: widget.onCancel,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                  decoration: BoxDecoration(
                                    color: Colors.transparent,
                                    borderRadius: BorderRadius.circular(10),
                                    border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
                                  ),
                                  child: Text(
                                    'Cancel',
                                    style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 12),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              // Approve
                              GestureDetector(
                                onTap: approvedSteps.isEmpty
                                    ? null
                                    : () => widget.onApprove(approvedSteps),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                                  decoration: BoxDecoration(
                                    color: approvedSteps.isEmpty
                                        ? Colors.white.withValues(alpha: 0.05)
                                        : const Color(0xFF2D7D2D),
                                    borderRadius: BorderRadius.circular(10),
                                    border: Border.all(
                                      color: approvedSteps.isEmpty
                                          ? Colors.white.withValues(alpha: 0.05)
                                          : Colors.greenAccent.withValues(alpha: 0.3),
                                    ),
                                    boxShadow: approvedSteps.isEmpty
                                        ? []
                                        : [
                                            BoxShadow(
                                              color: Colors.green.withValues(alpha: 0.2),
                                              blurRadius: 10,
                                            )
                                          ],
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(Icons.check_circle_outline,
                                          size: 14,
                                          color: approvedSteps.isEmpty
                                              ? Colors.white24
                                              : Colors.white),
                                      const SizedBox(width: 6),
                                      Text(
                                        'Approve & Run',
                                        style: TextStyle(
                                          color: approvedSteps.isEmpty ? Colors.white24 : Colors.white,
                                          fontSize: 12,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _UserMessageEditor extends StatefulWidget {
  final String initialText;
  final Widget markdownBody;
  final Function(String) onSave;
  final VoidCallback onCopy;

  const _UserMessageEditor({
    Key? key,
    required this.initialText,
    required this.markdownBody,
    required this.onSave,
    required this.onCopy,
  }) : super(key: key);

  @override
  State<_UserMessageEditor> createState() => _UserMessageEditorState();
}

class _UserMessageEditorState extends State<_UserMessageEditor> {
  bool _isEditing = false;
  bool _isHovered = false;
  late TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialText);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_isEditing) {
      return MouseRegion(
        onEnter: (_) => setState(() => _isHovered = true),
        onExit: (_) => setState(() => _isHovered = false),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF2A2A2A),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(24),
                  topRight: Radius.circular(24),
                  bottomLeft: Radius.circular(24),
                  bottomRight: Radius.circular(4),
                ),
                border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
              ),
              child: widget.markdownBody,
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (_isHovered) ...[
                  Tooltip(
                    message: "Copy",
                    preferBelow: true,
                    textStyle: const TextStyle(color: Colors.white, fontSize: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF2A2A2A),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
                    ),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(8),
                        hoverColor: Colors.white.withValues(alpha: 0.1),
                        onTap: widget.onCopy,
                        child: Padding(
                          padding: const EdgeInsets.all(8.0),
                          child: Icon(Icons.copy_outlined, size: 16, color: Colors.white.withValues(alpha: 0.6)),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 4),
                  Tooltip(
                    message: "Edit message",
                    preferBelow: true,
                    textStyle: const TextStyle(color: Colors.white, fontSize: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF2A2A2A),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
                    ),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(8),
                        hoverColor: Colors.white.withValues(alpha: 0.1),
                        onTap: () => setState(() => _isEditing = true),
                        child: Padding(
                          padding: const EdgeInsets.all(8.0),
                          child: Icon(Icons.edit_outlined, size: 16, color: Colors.white.withValues(alpha: 0.6)),
                        ),
                      ),
                    ),
                  ),
                ] else
                  const SizedBox(height: 32), // Placeholder to prevent jump
              ],
            )
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF2A2A2A),
        borderRadius: const BorderRadius.only(
          topLeft: Radius.circular(24),
          topRight: Radius.circular(24),
          bottomLeft: Radius.circular(24),
          bottomRight: Radius.circular(4),
        ),
        border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          TextField(
            controller: _controller,
            style: const TextStyle(color: Colors.white, fontSize: 15),
            maxLines: null,
            decoration: InputDecoration(
              isDense: true,
              filled: true,
              fillColor: const Color(0xFF2B2B2B),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton(
                onPressed: () {
                  setState(() {
                    _isEditing = false;
                    _controller.text = widget.initialText;
                  });
                },
                child: const Text("Cancel", style: TextStyle(color: Colors.white54)),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  minimumSize: const Size(0, 36),
                ),
                onPressed: () {
                  setState(() => _isEditing = false);
                  widget.onSave(_controller.text);
                },
                child: const Text("Submit", style: TextStyle(fontWeight: FontWeight.bold)),
              )
            ],
          )
        ],
      ),
    );
  }
}

class _SentAttachmentPill extends StatelessWidget {
  final String name;
  final String type;
  final String? base64Data;
  final String ext;

  const _SentAttachmentPill({
    required this.name,
    required this.type,
    this.base64Data,
    required this.ext,
  });

  @override
  Widget build(BuildContext context) {
    Color extColor = Colors.grey;
    if (ext == 'pdf') extColor = Colors.redAccent;
    else if (ext == 'doc' || ext == 'docx') extColor = Colors.blueAccent;
    else if (ext == 'xls' || ext == 'xlsx') extColor = Colors.green;
    else if (ext == 'txt') extColor = Colors.white70;
    else extColor = Colors.orangeAccent;

    return Container(
      margin: const EdgeInsets.only(right: 8, bottom: 8),
      constraints: const BoxConstraints(maxWidth: 240),
      width: type == 'image' ? 120 : null,
      height: type == 'image' ? 120 : null,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.15)),
        color: type == 'image' ? null : const Color(0xFF2C2C2C),
        image: type == 'image' && base64Data != null
            ? DecorationImage(
                image: MemoryImage(base64Decode(base64Data!)),
                fit: BoxFit.cover,
              )
            : null,
      ),
      child: type != 'image'
          ? Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14.0, vertical: 10.0),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                    decoration: BoxDecoration(
                      border: Border.all(color: extColor.withValues(alpha: 0.5)),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(ext.toUpperCase(), style: TextStyle(color: extColor, fontSize: 8, fontWeight: FontWeight.bold)),
                  ),
                  const SizedBox(width: 8),
                  Flexible(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(name,
                            style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis),
                        const SizedBox(height: 2),
                        Text("DOCUMENT",
                            style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 10, fontWeight: FontWeight.w500)),
                      ],
                    ),
                  ),
                ],
              ),
            )
          : null,
    );
  }
}

class HoverableAttachmentPill extends StatefulWidget {
  final dynamic file;
  final VoidCallback onRemove;

  const HoverableAttachmentPill({required this.file, required this.onRemove});

  @override
  State<HoverableAttachmentPill> createState() => HoverableAttachmentPillState();
}

class HoverableAttachmentPillState extends State<HoverableAttachmentPill> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    String filename = widget.file.name;
    String ext = filename.contains('.') ? filename.split('.').last.toLowerCase() : 'file';
    Color extColor = Colors.grey;
    if (ext == 'pdf') extColor = Colors.redAccent;
    else if (ext == 'doc' || ext == 'docx') extColor = Colors.blueAccent;
    else if (ext == 'xls' || ext == 'xlsx') extColor = Colors.green;
    else if (ext == 'txt') extColor = Colors.white70;
    else extColor = Colors.orangeAccent;

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Container(
            margin: const EdgeInsets.only(right: 8, top: 4),
            constraints: const BoxConstraints(maxWidth: 240),
            width: widget.file.type == 'image' ? 50 : null,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.white.withValues(alpha: 0.15)),
              color: widget.file.type == 'image' ? null : const Color(0xFF2C2C2C),
              image: widget.file.type == 'image'
                  ? DecorationImage(
                      image: MemoryImage(base64Decode(widget.file.base64Data)),
                      fit: BoxFit.cover,
                    )
                  : null,
            ),
            child: widget.file.type != 'image'
                ? Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 14.0, vertical: 10.0),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                          decoration: BoxDecoration(
                            border: Border.all(color: extColor.withValues(alpha: 0.5)),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(ext.toUpperCase(), style: TextStyle(color: extColor, fontSize: 8, fontWeight: FontWeight.bold)),
                        ),
                        const SizedBox(width: 8),
                        Flexible(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(widget.file.name,
                                  style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis),
                              const SizedBox(height: 2),
                              Text("DOCUMENT",
                                  style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 10, fontWeight: FontWeight.w500)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  )
                : null,
          ),
          if (_isHovered)
            Positioned(
              right: 0,
              top: 0,
              child: InkWell(
                onTap: widget.onRemove,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(color: Colors.black26, blurRadius: 4, offset: Offset(0, 2))
                    ],
                  ),
                  child: const Icon(Icons.close, size: 10, color: Colors.black87),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
