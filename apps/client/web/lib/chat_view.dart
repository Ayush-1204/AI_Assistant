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
import 'api_client.dart';
import 'providers/auth_provider.dart';
import 'providers/chat_provider.dart';

class LoadingDots extends StatefulWidget {
  const LoadingDots({super.key});
  @override
  State<LoadingDots> createState() => _LoadingDotsState();
}

class _LoadingDotsState extends State<LoadingDots> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(milliseconds: 1000))..repeat();
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
            if (progress >= 0 && progress <= 1) offset = -5 * (0.5 - (progress - 0.5).abs()) * 2;
            return Container(
              margin: const EdgeInsets.symmetric(horizontal: 2),
              transform: Matrix4.translationValues(0, offset, 0),
              width: 6, height: 6,
              decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.6), shape: BoxShape.circle),
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

class _ActiveVoiceBarState extends ConsumerState<ActiveVoiceBar> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1500))..repeat();
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
              Text('.......', style: TextStyle(color: Colors.white.withValues(alpha: 0.2), letterSpacing: 2)),
              const SizedBox(width: 8),
              Expanded(
                child: Consumer(builder: (context, ref, _) {
                  final transcript = ref.watch(chatProvider).liveTranscript;
                  return Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(24, (index) {
                      double amplitude = transcript.isNotEmpty ? 16.0 : 4.0;
                      double height = 4.0 + amplitude * (0.5 + 0.5 * math.sin((val * 2 * math.pi) + (index * 0.4)));
                      return Container(
                        width: 3,
                        height: height,
                        margin: const EdgeInsets.symmetric(horizontal: 1.5),
                        decoration: BoxDecoration(
                           color: Colors.white.withValues(alpha: 0.6),
                           borderRadius: BorderRadius.circular(1.5),
                        )
                      );
                    }),
                  );
                }),
              ),
              const SizedBox(width: 8),
              InkWell(
                onTap: () {
                   final p = ref.read(chatProvider.notifier);
                   if (ref.read(chatProvider).isListening) p.toggleListening(); 
                   if (ref.read(chatProvider).isVoiceTyping) p.toggleVoiceTyping();
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

class TypewriterMarkdown extends StatefulWidget {
  final String text;
  const TypewriterMarkdown({super.key, required this.text});
  @override
  State<TypewriterMarkdown> createState() => _TypewriterMarkdownState();
}
class _TypewriterMarkdownState extends State<TypewriterMarkdown> {
  String displayedText = '';
  Timer? _timer;
  @override
  void initState() {
    super.initState();
    _animateText();
  }
  @override
  void didUpdateWidget(covariant TypewriterMarkdown oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.text != widget.text) _animateText();
  }
  void _animateText() {
    _timer?.cancel();
    displayedText = '';
    int index = 0;
    _timer = Timer.periodic(const Duration(milliseconds: 10), (timer) {
      if (index < widget.text.length) {
        setState(() {
          displayedText += widget.text[index];
          index++;
        });
      } else {
        timer.cancel();
      }
    });
  }
  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
  @override
  Widget build(BuildContext context) {
    return MarkdownBody(
      data: displayedText,
      selectable: true,
      styleSheet: MarkdownStyleSheet(
        p: TextStyle(fontSize: 15, height: 1.5, color: Colors.white.withValues(alpha: 0.9)),
      ),
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

  @override
  void initState() {
    super.initState();
    _initLocation();
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

  void _showEditTitleDialog(int id, String currentTitle) {
    final tc = TextEditingController(text: currentTitle);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1B1B1B),
        title: const Text('Edit Conversation Title', style: TextStyle(color: Colors.white)),
        content: TextField(
          controller: tc,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: 'Enter new title',
            hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.4)),
            enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.1))),
            focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Theme.of(context).colorScheme.primary)),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            onPressed: () {
               if (tc.text.trim().isNotEmpty) {
                 ref.read(chatProvider.notifier).updateChatTitle(id, tc.text.trim());
               }
               Navigator.pop(ctx);
            },
            style: ElevatedButton.styleFrom(backgroundColor: Theme.of(context).colorScheme.primary),
            child: const Text('Save', style: TextStyle(color: Colors.white)),
          ),
        ],
      )
    );
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
            color: Theme.of(context).colorScheme.surface.withValues(alpha: 0.8),
            border: Border(bottom: BorderSide(color: Colors.white.withValues(alpha: 0.05))),
          ),
          child: Row(
            children: [
              const Text('Workspace Overview', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600, letterSpacing: -0.5, color: Colors.white)),
              const Spacer(),
              ElevatedButton.icon(
                onPressed: () => ref.read(chatProvider.notifier).startNewChat(),
                icon: const Icon(Icons.add_comment, size: 16),
                label: const Text('New Chat'),
                style: ElevatedButton.styleFrom(
                   backgroundColor: Theme.of(context).colorScheme.primary.withValues(alpha: 0.15),
                   foregroundColor: Theme.of(context).colorScheme.primary,
                   elevation: 0,
                   shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                   padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
              ),
              const SizedBox(width: 16),
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
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              s['title']?.toString() ?? 'Session ${s['id']}',
                              style: TextStyle(color: isActive ? Theme.of(context).colorScheme.primary : Colors.white70),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              InkWell(
                                onTap: () {
                                  Navigator.pop(context); // Close dropdown organically
                                  _showEditTitleDialog(s['id'] as int, s['title']?.toString() ?? '');
                                },
                                child: Icon(Icons.edit, size: 14, color: Colors.white.withValues(alpha: 0.5)),
                              ),
                              const SizedBox(width: 8),
                              InkWell(
                                onTap: () {
                                  Navigator.pop(context); // Close dropdown organically
                                  ref.read(chatProvider.notifier).deleteChat(s['id'] as int);
                                },
                                child: Icon(Icons.delete_outline, size: 14, color: Colors.redAccent.withValues(alpha: 0.8)),
                              ),
                            ]
                          )
                        ],
                      ),
                    );
                  }).toList(),
                  child: _buildHeaderAction(Icons.history, "Recent", active: true),
                );
              }),
              _buildHeaderDivider(),
              _buildHeaderAction(Icons.push_pin, "Pinned"),
              const SizedBox(width: 16),
              IconButton(icon: const Icon(Icons.more_vert), onPressed: () {}, color: Colors.white.withValues(alpha: 0.6)),
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
              itemCount: chatState.messages.length + 1 + (chatState.isSending ? 1 : 0),
              itemBuilder: (context, index) {
                if (index == 0) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 32.0),
                    child: _buildDashboardWidgets(),
                  );
                }
                
                // Loading indicator logic
                if (chatState.isSending && index == chatState.messages.length + 1) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 24.0),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          margin: const EdgeInsets.only(right: 16),
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.15),
                            shape: BoxShape.circle,
                            border: Border.all(color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.3)),
                          ),
                          child: Icon(Icons.auto_awesome, color: Theme.of(context).colorScheme.primary, size: 20),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                          decoration: BoxDecoration(
                            color: const Color(0xFF1B1B1B).withValues(alpha: 0.9),
                            borderRadius: const BorderRadius.only(topLeft: Radius.circular(24), topRight: Radius.circular(24), bottomLeft: Radius.circular(4), bottomRight: Radius.circular(24)),
                            border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
                          ),
                          child: const LoadingDots(),
                        ),
                      ],
                    ),
                  );
                }
                
                final msg = chatState.messages[index - 1];
                final isAssistant = msg.startsWith("Assistant:");
              final displayMsg = isAssistant ? msg.replaceFirst("Assistant:", "").trim() : msg;
              
              // Only animate the very last assistant message if it just arrived
              bool isLatestAssistant = isAssistant && (index - 1 == chatState.messages.length - 1) && !chatState.isSending;
              
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
                          color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.15),
                          shape: BoxShape.circle,
                          border: Border.all(color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.3)),
                        ),
                        child: Icon(Icons.auto_awesome, color: Theme.of(context).colorScheme.primary, size: 20),
                      ),
                    Flexible(
                      child: Container(
                        padding: isAssistant ? const EdgeInsets.only(top: 8, bottom: 8) : const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: isAssistant ? Colors.transparent : const Color(0xFF2A2A2A),
                          borderRadius: BorderRadius.only(
                            topLeft: const Radius.circular(24),
                            topRight: const Radius.circular(24),
                            bottomLeft: isAssistant ? const Radius.circular(4) : const Radius.circular(24),
                            bottomRight: isAssistant ? const Radius.circular(24) : const Radius.circular(4),
                          ),
                          border: isAssistant ? null : Border.all(color: Colors.white.withValues(alpha: 0.05)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            isLatestAssistant 
                              ? TypewriterMarkdown(text: displayMsg)
                              : MarkdownBody(
                                  data: displayMsg,
                                  selectable: true,
                                  styleSheet: MarkdownStyleSheet(
                                    p: TextStyle(fontSize: 15, height: 1.5, color: Colors.white.withValues(alpha: 0.9)),
                                  ),
                                ),
                            if (isAssistant && chatState.messageMetadata[index - 1] != null) ...[
                               if (chatState.messageMetadata[index - 1]!['requires_confirmation'] == true)
                                  _PlanApprovalRequestPanel(metadata: chatState.messageMetadata[index - 1]!),
                               _ExplainabilityPanel(metadata: chatState.messageMetadata[index - 1]),
                            ],
                            const SizedBox(height: 12),
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                InkWell(
                                  onTap: () {
                                    Clipboard.setData(ClipboardData(text: displayMsg));
                                  },
                                  child: Icon(Icons.copy_outlined, size: 16, color: Colors.white.withValues(alpha: 0.5)),
                                ),
                                if (isAssistant) ...[
                                  const SizedBox(width: 16),
                                  InkWell(
                                    onTap: () => ref.read(chatProvider.notifier).readAloud(displayMsg),
                                    child: Icon(Icons.volume_up_outlined, size: 16, color: Colors.white.withValues(alpha: 0.5)),
                                  ),
                                  const SizedBox(width: 16),
                                  InkWell(
                                    onTap: () {},
                                    child: Icon(Icons.thumb_up_outlined, size: 16, color: Colors.white.withValues(alpha: 0.5)),
                                  ),
                                  const SizedBox(width: 16),
                                  InkWell(
                                    onTap: () {},
                                    child: Icon(Icons.thumb_down_outlined, size: 16, color: Colors.white.withValues(alpha: 0.5)),
                                  ),
                                  const SizedBox(width: 16),
                                  InkWell(
                                    onTap: () => ref.read(chatProvider.notifier).regenerateLastResponse(),
                                    child: Icon(Icons.refresh, size: 16, color: Colors.white.withValues(alpha: 0.5)),
                                  ),
                                ]
                              ],
                            )
                          ],
                        ),
                      ),
                    ),
                    if (!isAssistant)
                      Container(
                        margin: const EdgeInsets.only(left: 16),
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.1),
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
                        ),
                        child: Icon(Icons.person, color: Colors.white.withValues(alpha: 0.8), size: 20),
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
                    color: const Color(0xFF131313).withValues(alpha: 0.95),
                    borderRadius: BorderRadius.circular(32),
                    border: Border.all(color: Colors.white.withValues(alpha: 0.15)),
                    boxShadow: [
                      BoxShadow(color: Colors.black.withValues(alpha: 0.5), blurRadius: 24, offset: const Offset(0, 10))
                    ],
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (ref.watch(chatProvider).pendingImages.isNotEmpty)
                        Container(
                          height: 60,
                          alignment: Alignment.centerLeft,
                          padding: const EdgeInsets.only(bottom: 8),
                          child: ListView.builder(
                            scrollDirection: Axis.horizontal,
                            itemCount: ref.watch(chatProvider).pendingImages.length,
                            itemBuilder: (context, idx) {
                               final b64 = ref.watch(chatProvider).pendingImages[idx];
                               return Stack(
                                 children: [
                                   Container(
                                     margin: const EdgeInsets.only(right: 8),
                                     width: 50,
                                     decoration: BoxDecoration(
                                       borderRadius: BorderRadius.circular(8),
                                       border: Border.all(color: Colors.white.withValues(alpha: 0.2)),
                                       image: DecorationImage(
                                          image: MemoryImage(base64Decode(b64)),
                                          fit: BoxFit.cover,
                                       ),
                                     ),
                                   ),
                                   Positioned(
                                     right: 0,
                                     top: -4,
                                     child: InkWell(
                                       onTap: () => ref.read(chatProvider.notifier).clearAttachments(),
                                       child: Container(
                                         padding: const EdgeInsets.all(2),
                                         decoration: const BoxDecoration(color: Colors.black54, shape: BoxShape.circle),
                                         child: const Icon(Icons.close, size: 12, color: Colors.white),
                                       ),
                                     ),
                                   )
                                 ],
                               );
                            }
                          )
                        ),
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          PopupMenuButton<String>(
                            icon: const Icon(Icons.attach_file, size: 22, color: Colors.white60),
                            color: const Color(0xFF1B1B1B),
                            offset: const Offset(0, -100),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                            onSelected: (value) async {
                              if (value == 'document') {
                                _pickAndUploadFile();
                              } else if (value == 'image') {
                                FilePickerResult? result = await FilePicker.pickFiles(type: FileType.image, withData: true);
                                if (result != null && result.files.single.bytes != null) {
                                   String base64Img = base64Encode(result.files.single.bytes!);
                                   ref.read(chatProvider.notifier).attachImage(base64Img);
                                }
                              }
                            },
                            itemBuilder: (BuildContext context) => <PopupMenuEntry<String>>[
                              const PopupMenuItem<String>(
                                value: 'image',
                                child: Row(
                                  children: [
                                    Icon(Icons.image, color: Colors.white70, size: 20),
                                    SizedBox(width: 12),
                                    Text('Attach Image to Message', style: TextStyle(color: Colors.white)),
                                  ]
                                ),
                              ),
                              const PopupMenuItem<String>(
                                value: 'document',
                                child: Row(
                                  children: [
                                    Icon(Icons.upload_file, color: Colors.white70, size: 20),
                                    SizedBox(width: 12),
                                    Text('Upload Document to Memory', style: TextStyle(color: Colors.white)),
                                  ]
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(width: 4),
                          Expanded(
                            child: (isListening || ref.watch(chatProvider).isVoiceTyping)
                                ? const ActiveVoiceBar()
                                : TextField(
                                    controller: _controller,
                                    keyboardType: TextInputType.multiline,
                                    minLines: 1,
                                    maxLines: 5,
                                    style: const TextStyle(fontSize: 15, color: Colors.white),
                                    decoration: InputDecoration(
                                      hintText: 'Message Aura AI or type "/" for commands...',
                                      hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.4)),
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
                          color: Colors.white.withValues(alpha: 0.05),
                          borderRadius: BorderRadius.circular(24),
                          border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            IconButton(
                              tooltip: 'Voice Typing',
                              constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                              padding: EdgeInsets.zero,
                              icon: Icon(ref.watch(chatProvider).isVoiceTyping ? Icons.stop_circle : Icons.mic_none, size: 20),
                              color: ref.watch(chatProvider).isVoiceTyping ? Colors.redAccent : Colors.white.withValues(alpha: 0.6),
                              onPressed: () {
                                ref.read(chatProvider.notifier).toggleVoiceTyping();
                              },
                            ),
                            IconButton(
                              tooltip: 'Live Voice Mode',
                              constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                              padding: EdgeInsets.zero,
                              icon: Icon(isListening ? Icons.phone_disabled : Icons.phone_in_talk, size: 20),
                              color: isListening ? Colors.redAccent : Colors.blueAccent.withValues(alpha: 0.8),
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
                              boxShadow: [BoxShadow(color: Colors.white.withValues(alpha: 0.2), blurRadius: 8)],
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
                      ), // End Action buttons row
                    ), // End Action buttons container
                  ], // End main Row children
                ), // End main Row
              ], // End main Column children
            ), // End main Column
          ), // End BoxConstraints Container
        ), // End Align
      ), // End SafeArea
    ); // End main Container
  }), // End Consumer
      ], // End of Column children
      ), // End of Column

      ], // End of Stack children
    ); // End of Stack
  }

  Widget _buildHeaderAction(IconData icon, String label, {bool active = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Row(
        children: [
          Icon(icon, size: 18, color: active ? Theme.of(context).colorScheme.primary : Colors.white.withValues(alpha: 0.6)),
          const SizedBox(width: 8),
          Text(label, style: TextStyle(
            fontSize: 14, 
            fontWeight: FontWeight.w500, 
            color: active ? Theme.of(context).colorScheme.primary : Colors.white.withValues(alpha: 0.6),
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
        boxShadow: [BoxShadow(color: Colors.orangeAccent.withValues(alpha: 0.05), blurRadius: 20)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: Colors.orangeAccent, size: 20),
              SizedBox(width: 8),
              Text('Approval Required', style: TextStyle(color: Colors.orangeAccent, fontWeight: FontWeight.bold, fontSize: 14)),
            ],
          ),
          const SizedBox(height: 12),
          Text(metadata['pending_tool_name'] ?? 'Agent Plan Execution', style: const TextStyle(fontWeight: FontWeight.w600, color: Colors.white, fontSize: 16)),
          const SizedBox(height: 4),
          Text('The agent requires confirmation before proceeding with this action natively.', style: TextStyle(fontSize: 13, color: Colors.white.withValues(alpha: 0.6))),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton(
                onPressed: () {},
                child: const Text('Reject', style: TextStyle(color: Colors.redAccent)),
              ),
              const SizedBox(width: 12),
              ElevatedButton.icon(
                onPressed: () {},
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orangeAccent,
                  foregroundColor: Colors.black,
                  elevation: 0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
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
              Icon(Icons.info_outline, size: 14, color: Colors.blueAccent.withValues(alpha: 0.8)),
              const SizedBox(width: 6),
              Text("Why did you say that?", style: TextStyle(color: Colors.blueAccent.withValues(alpha: 0.8), fontSize: 12)),
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
                _buildMetaRow("Model / Routing", widget.metadata!['model_used']?.toString() ?? "Provider API"),
                const SizedBox(height: 4),
                _buildMetaRow("Retrieved Sources", "${widget.metadata!['retrieval_chunks'] ?? 0} contextual chunks"),
                const SizedBox(height: 4),
                _buildMetaRow("Execution Latency", "${widget.metadata!['latency_ms'] ?? 0} ms"),
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
        Text("$label: ", style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 11)),
        Text(value, style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 11, fontFamily: 'monospace')),
      ],
    );
  }
}

class _SkeletonDashboardCard extends StatefulWidget {
  const _SkeletonDashboardCard();

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
                  BoxShadow(color: Colors.black.withValues(alpha: 0.2), blurRadius: 40, spreadRadius: -10)
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
                  Container(width: double.infinity, height: 12, decoration: BoxDecoration(color: Colors.white.withValues(alpha: opacity * 0.7), borderRadius: BorderRadius.circular(4))),
                  const SizedBox(height: 8),
                  Container(width: 180, height: 12, decoration: BoxDecoration(color: Colors.white.withValues(alpha: opacity * 0.7), borderRadius: BorderRadius.circular(4))),
                  const SizedBox(height: 16),
                  Expanded(
                    child: Container(width: double.infinity, decoration: BoxDecoration(color: Colors.white.withValues(alpha: opacity * 0.5), borderRadius: BorderRadius.circular(16))),
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
  const _DashboardWidgetCard({required this.data, required this.index});
  @override
  State<_DashboardWidgetCard> createState() => _DashboardWidgetCardState();
}

class _DashboardWidgetCardState extends State<_DashboardWidgetCard> with AutomaticKeepAliveClientMixin {
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
                Text(w['subtitle'] ?? '', style: TextStyle(fontSize: 13, color: Colors.white.withValues(alpha: 0.5))),
              ],
            ),
            const AnimatedWeatherIcon(),
          ],
        ),
        if (w['ai_summary'] != null && w['ai_summary'].toString().isNotEmpty) ...[
          const SizedBox(height: 16),
          Expanded(
             child: Text(w['ai_summary'] ?? '', style: TextStyle(fontSize: 13, height: 1.4, color: Colors.white.withValues(alpha: 0.8)), maxLines: 3, overflow: TextOverflow.ellipsis),
          ),
        ] else const Spacer(),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: forecast.map((f) {
            return Column(
              children: [
                Text(f['day'].toString(), style: TextStyle(fontSize: 11, color: Colors.white.withValues(alpha: 0.5))),
                const SizedBox(height: 4),
                Icon(Icons.wb_sunny, size: 16, color: Colors.white.withValues(alpha: 0.8)),
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
                Text(w['badge'] ?? '', style: TextStyle(fontSize: 12, color: Colors.white.withValues(alpha: 0.5))),
              ],
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(color: Colors.indigoAccent.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(12)),
              child: const Text('Today', style: TextStyle(color: Colors.indigoAccent, fontSize: 11, fontWeight: FontWeight.bold)),
            )
          ],
        ),
        if (w['ai_summary'] != null && w['ai_summary'].toString().isNotEmpty) ...[
          const SizedBox(height: 12),
          Text(w['ai_summary'] ?? '', style: TextStyle(fontSize: 13, height: 1.4, color: Colors.white.withValues(alpha: 0.8)), maxLines: 2, overflow: TextOverflow.ellipsis),
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
                      color: isToday ? Colors.indigoAccent : (isEvent ? Colors.white.withValues(alpha: 0.08) : Colors.transparent),
                      shape: BoxShape.circle,
                    ),
                    alignment: Alignment.center,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Flexible(child: Text(d['day'].toString(), style: TextStyle(fontSize: 12, fontWeight: isToday ? FontWeight.bold : FontWeight.normal, color: Colors.white.withValues(alpha: isToday ? 1.0 : 0.6)))),
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
                              decoration: BoxDecoration(color: Colors.green.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(12)),
                              child: Text(article['domain'].toString().toUpperCase(), style: const TextStyle(color: Colors.greenAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Text(article['title'] ?? '', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white, height: 1.2), maxLines: 2, overflow: TextOverflow.ellipsis),
                        const SizedBox(height: 12),
                        Expanded(
                          child: Text(article['summary'] ?? '', style: TextStyle(fontSize: 13, height: 1.6, color: Colors.white.withValues(alpha: 0.6)), overflow: TextOverflow.fade),
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
                    IconButton(icon: Icon(Icons.chevron_left, color: Colors.white.withValues(alpha: 0.5)), onPressed: () { _pageController.previousPage(duration: const Duration(milliseconds: 300), curve: Curves.ease); }),
                    IconButton(icon: Icon(Icons.chevron_right, color: Colors.white.withValues(alpha: 0.5)), onPressed: () { _pageController.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.ease); }),
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
                        color: const Color(0xFF1F1F1F).withValues(alpha: 0.35),
                        borderRadius: BorderRadius.circular(32),
                        border: Border.all(color: Colors.white.withValues(alpha: _isHovered ? 0.15 : 0.05)),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: _isHovered ? 0.3 : 0.1), 
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
