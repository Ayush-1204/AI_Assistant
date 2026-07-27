import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:markdown/markdown.dart' as md;
import 'package:flutter_highlighter/themes/atom-one-dark.dart';
import 'selectable_highlight_view.dart';

class CodeBlockBuilder extends MarkdownElementBuilder {
  final BuildContext context;
  
  CodeBlockBuilder(this.context);

  @override
  Widget? visitElementAfter(md.Element element, TextStyle? preferredStyle) {
    // Fenced code blocks are parsed as <pre><code>...</code></pre>
    // We are binding this builder to the 'pre' tag.
    
    String textContent = element.textContent.trimRight();
    
    String language = 'plaintext';
    if (element.children != null && element.children!.isNotEmpty) {
      final codeElement = element.children!.first;
      if (codeElement is md.Element && codeElement.attributes['class'] != null) {
        String langClass = codeElement.attributes['class']!;
        if (langClass.startsWith('language-')) {
          language = langClass.replaceFirst('language-', '');
        }
      }
    }

    return Container(
      margin: const EdgeInsets.only(top: 16, bottom: 24),
      decoration: BoxDecoration(
        color: const Color(0xFF0D0D0D), // Sleek ChatGPT dark background
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFF212121), // Sleek header
              border: Border(
                bottom: BorderSide(color: Colors.white.withValues(alpha: 0.05))
              )
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text(
                      '</> ',
                      style: TextStyle(
                        color: Colors.white54,
                        fontSize: 12,
                        fontFamily: 'monospace',
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      language.toLowerCase(),
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 12,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                _CopyButton(text: textContent),
              ],
            ),
          ),
          // Code Content
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: SelectableHighlightView(
              textContent,
              padding: const EdgeInsets.all(16),
              language: language,
              theme: Map<String, TextStyle>.from(atomOneDarkTheme)
                ..['root'] = TextStyle(
                  backgroundColor: Colors.transparent, // Fix the boxed-in background
                  color: const Color(0xffabb2bf),
                ),
              textStyle: const TextStyle(
                fontFamily: 'monospace',
                fontSize: 13,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CopyButton extends StatefulWidget {
  final String text;
  
  const _CopyButton({Key? key, required this.text}) : super(key: key);

  @override
  __CopyButtonState createState() => __CopyButtonState();
}

class __CopyButtonState extends State<_CopyButton> {
  bool _copied = false;

  void _copy() {
    Clipboard.setData(ClipboardData(text: widget.text));
    setState(() => _copied = true);
    Future.delayed(const Duration(seconds: 2), () {
      if (mounted) {
        setState(() => _copied = false);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: _copy,
      borderRadius: BorderRadius.circular(4),
      child: Padding(
        padding: const EdgeInsets.all(4.0),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              _copied ? Icons.check : Icons.copy_outlined,
              size: 14,
              color: _copied ? Colors.green : Colors.white70,
            ),
            const SizedBox(width: 4),
            Text(
              _copied ? "Copied" : "Copy code",
              style: TextStyle(
                color: _copied ? Colors.green : Colors.white70,
                fontSize: 12,
              ),
            )
          ],
        ),
      ),
    );
  }
}
