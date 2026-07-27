import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:markdown/markdown.dart' as md;

class InlineCodeBuilder extends MarkdownElementBuilder {
  final BuildContext context;

  InlineCodeBuilder(this.context);

  @override
  Widget? visitElementAfter(md.Element element, TextStyle? preferredStyle) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: Colors.white.withValues(alpha: 0.15)),
      ),
      child: Text(
        element.textContent,
        style: TextStyle(
          fontFamily: 'monospace',
          fontSize: (preferredStyle?.fontSize ?? 15) * 0.9,
          color: Colors.orangeAccent.shade100,
        ),
      ),
    );
  }
}
