import 'package:flutter/material.dart';
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
          return const SizedBox(height: 24, child: Center(child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)));
        }
        
        final widgets = snapshot.data!;
        return GridView.count(
          crossAxisCount: crossAxisCount,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          childAspectRatio: screenWidth > 800 ? 1.6 : 2.0,
          children: List.generate(widgets.length, (index) {
            final w = widgets[index];
            final iconMap = {'light_mode': Icons.light_mode, 'calendar_month': Icons.calendar_month, 'public': Icons.public, 'checklist': Icons.checklist};
            return _DashboardWidgetCard(
              iconMap[w['icon']] ?? Icons.widgets, 
              Color(int.parse(w['color_hex'], radix: 16)),
              w['badge'], 
              w['title'], 
              w['subtitle'],
              index
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
              _buildHeaderAction(Icons.history, "Recent", active: true),
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

class _DashboardWidgetCard extends StatefulWidget {
  final IconData icon;
  final Color color;
  final String badge;
  final String title;
  final String subtitle;
  final int index;
  
  const _DashboardWidgetCard(this.icon, this.color, this.badge, this.title, this.subtitle, this.index);

  @override
  State<_DashboardWidgetCard> createState() => _DashboardWidgetCardState();
}

class _DashboardWidgetCardState extends State<_DashboardWidgetCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
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
                scale: _isHovered ? 1.03 : 1.0,
                duration: const Duration(milliseconds: 200),
                curve: Curves.easeOutCubic,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.all(20),
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
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Container(padding: const EdgeInsets.all(8), decoration: BoxDecoration(color: widget.color.withOpacity(0.1), borderRadius: BorderRadius.circular(8)), child: Icon(widget.icon, color: widget.color, size: 20)),
                          Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4), decoration: BoxDecoration(color: widget.color.withOpacity(0.1), borderRadius: BorderRadius.circular(16)), child: Text(widget.badge, style: TextStyle(color: widget.color, fontSize: 12, fontWeight: FontWeight.w600))),
                        ],
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(widget.title, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w600, color: Colors.white, height: 1.2, letterSpacing: -0.5)),
                          const SizedBox(height: 4),
                          Text(widget.subtitle, style: TextStyle(fontSize: 14, color: Colors.white.withOpacity(0.5))),
                        ],
                      ),
                    ],
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
