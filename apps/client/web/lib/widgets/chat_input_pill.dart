import 'dart:convert';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/chat_provider.dart';
import '../chat_view.dart'; // To get ActiveVoiceBar, WaveformCircleIcon, HoverableAttachmentPill

class ChatInputPill extends ConsumerStatefulWidget {
  final TextEditingController controller;
  final VoidCallback onSend;

  const ChatInputPill({
    Key? key,
    required this.controller,
    required this.onSend,
  }) : super(key: key);

  @override
  ConsumerState<ChatInputPill> createState() => _ChatInputPillState();
}

class _ChatInputPillState extends ConsumerState<ChatInputPill> {
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

  @override
  Widget build(BuildContext context) {
    final isListening = ref.watch(chatProvider).isListening;
    final isProcessing = ref.watch(chatProvider).isProcessing;
    
    return Container(
      constraints: const BoxConstraints(maxWidth: 800),
      padding: const EdgeInsets.only(left: 12, right: 12, top: 8, bottom: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF131313),
        borderRadius: BorderRadius.circular(32),
        border: Border.all(color: Colors.white.withValues(alpha: 0.15)),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.5),
              blurRadius: 24,
              offset: const Offset(0, 10))
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (ref.watch(chatProvider).pendingFiles.isNotEmpty)
            Container(
                height: 75,
                alignment: Alignment.centerLeft,
                padding: const EdgeInsets.only(bottom: 8),
                child: ListView.builder(
                    scrollDirection: Axis.horizontal,
                    itemCount: ref.watch(chatProvider).pendingFiles.length,
                    itemBuilder: (context, idx) {
                      final file = ref.watch(chatProvider).pendingFiles[idx];
                      return HoverableAttachmentPill(
                        file: file,
                        onRemove: () => ref.read(chatProvider.notifier).removeAttachment(idx),
                      );
                    })),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Container(
                margin: const EdgeInsets.only(bottom: 2), // Align visually with text field
                child: IconButton(
                  constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
                  padding: EdgeInsets.zero,
                  splashRadius: 20,
                  icon: const Icon(Icons.attach_file, size: 24, color: Colors.white60),
                  onPressed: _pickUnifiedFile,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: (!ref.watch(chatProvider).isContinuousVoiceMode &&
                        (isListening || ref.watch(chatProvider).isVoiceTyping))
                    ? const ActiveVoiceBar()
                    : Focus(
                        onKeyEvent: (node, event) {
                          if (event is KeyDownEvent &&
                              event.logicalKey == LogicalKeyboardKey.enter) {
                            if (HardwareKeyboard.instance.isShiftPressed) {
                              return KeyEventResult.ignored;
                            } else {
                              widget.onSend();
                              return KeyEventResult.handled;
                            }
                          }
                          return KeyEventResult.ignored;
                        },
                        child: TextField(
                          controller: widget.controller,
                          keyboardType: TextInputType.multiline,
                          minLines: 1,
                          maxLines: 5,
                          style: const TextStyle(fontSize: 15, color: Colors.white),
                          decoration: InputDecoration(
                            hintText: 'Ask Anything...',
                            hintStyle: TextStyle(
                                color: Colors.white.withValues(alpha: 0.4)),
                            border: InputBorder.none,
                            isDense: true,
                            contentPadding: const EdgeInsets.only(left: 4, right: 4, top: 8, bottom: 12),
                          ),
                        ),
                      ),
              ),
              const SizedBox(width: 4),
              // Action buttons pill
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
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
                      splashRadius: 18,
                      icon: Icon(
                          ref.watch(chatProvider).isVoiceTyping
                              ? Icons.stop_circle
                              : Icons.mic_none,
                          size: 20),
                      color: ref.watch(chatProvider).isVoiceTyping
                          ? Colors.redAccent
                          : Colors.white.withValues(alpha: 0.6),
                      onPressed: () {
                        ref.read(chatProvider.notifier).toggleVoiceTyping();
                      },
                    ),
                    const SizedBox(width: 4),
                    ValueListenableBuilder<TextEditingValue>(
                      valueListenable: widget.controller,
                      builder: (context, value, child) {
                        bool isEmpty = value.text.trim().isEmpty;
                        if (ref.watch(chatProvider).isContinuousVoiceMode) {
                          return IconButton(
                            tooltip: 'End Voice Mode',
                            constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                            padding: EdgeInsets.zero,
                            splashRadius: 18,
                            icon: const Icon(Icons.close, color: Colors.white54, size: 28),
                            onPressed: () {
                              final notifier = ref.read(chatProvider.notifier);
                              notifier.setContinuousVoiceMode(false);
                              if (ref.read(chatProvider).isSpeaking) notifier.stopSpeaking();
                              if (ref.read(chatProvider).isListening ||
                                  ref.read(chatProvider).isVoiceTyping) {
                                notifier.stopListening();
                              }
                            },
                          );
                        } else if (isProcessing) {
                          return Container(
                            width: 36,
                            height: 36,
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(18),
                              boxShadow: [
                                BoxShadow(
                                    color: Colors.white.withValues(alpha: 0.2),
                                    blurRadius: 8)
                              ],
                            ),
                            child: IconButton(
                              padding: EdgeInsets.zero,
                              splashRadius: 18,
                              tooltip: 'Stop Generating',
                              icon: const Icon(Icons.stop, size: 22, color: Colors.black),
                              onPressed: () => ref.read(chatProvider.notifier).stopGenerating(),
                            ),
                          );
                        } else if (isEmpty) {
                          return IconButton(
                            tooltip: 'Live Voice Mode',
                            constraints: const BoxConstraints(minWidth: 36, minHeight: 36),
                            padding: EdgeInsets.zero,
                            splashRadius: 18,
                            icon: const WaveformCircleIcon(),
                            onPressed: () {
                              ref.read(chatProvider.notifier).setContinuousVoiceMode(true);
                            },
                          );
                        } else {
                          return Container(
                            width: 36,
                            height: 36,
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(18),
                              boxShadow: [
                                BoxShadow(
                                    color: Colors.white.withValues(alpha: 0.2),
                                    blurRadius: 8)
                              ],
                            ),
                            child: IconButton(
                              padding: EdgeInsets.zero,
                              splashRadius: 18,
                              tooltip: 'Send Message',
                              icon: const Icon(Icons.arrow_upward,
                                  size: 20, color: Colors.black),
                              onPressed: widget.onSend,
                            ),
                          );
                        }
                      },
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
}





class HoverableAttachmentPill extends StatefulWidget {
  final dynamic file;
  final VoidCallback onRemove;

  const HoverableAttachmentPill({Key? key, required this.file, required this.onRemove}) : super(key: key);

  @override
  _HoverableAttachmentPillState createState() => _HoverableAttachmentPillState();
}

class _HoverableAttachmentPillState extends State<HoverableAttachmentPill> {
  bool isHovering = false;

  @override
  Widget build(BuildContext context) {
    String filename = widget.file.name;
    String ext = filename.contains('.') ? filename.split('.').last.toLowerCase() : 'file';
    Color extColor = Colors.grey;
    String docType = 'DOCUMENT';
    
    if (ext == 'pdf') {
      extColor = Colors.redAccent;
      docType = 'PDF DOCUMENT';
    } else if (ext == 'doc' || ext == 'docx') {
      extColor = Colors.blueAccent;
      docType = 'WORD DOCUMENT';
    } else if (ext == 'xls' || ext == 'xlsx') {
      extColor = Colors.green;
      docType = 'EXCEL SPREADSHEET';
    } else if (ext == 'ppt' || ext == 'pptx') {
      extColor = Colors.orangeAccent;
      docType = 'POWERPOINT DOCUMENT';
    } else if (ext == 'md') {
      extColor = Colors.orange;
      docType = 'MARKDOWN DOCUMENT';
    } else if (ext == 'txt') {
      extColor = Colors.white70;
      docType = 'TEXT DOCUMENT';
    } else if (ext == 'csv') {
      extColor = Colors.greenAccent;
      docType = 'CSV DOCUMENT';
    } else {
      extColor = Colors.orangeAccent;
    }

    return MouseRegion(
      onEnter: (_) => setState(() => isHovering = true),
      onExit: (_) => setState(() => isHovering = false),
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
              image: widget.file.type == 'image' && widget.file.base64Data != null && widget.file.base64Data.isNotEmpty
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
                              Text(docType,
                                  style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 10, fontWeight: FontWeight.w500)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  )
                : null,
          ),
          if (isHovering)
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
