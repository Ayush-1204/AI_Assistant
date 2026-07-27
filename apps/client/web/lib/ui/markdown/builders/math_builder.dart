import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:markdown/markdown.dart' as md;
import 'package:flutter_math_fork/flutter_math.dart';

class MathBuilder extends MarkdownElementBuilder {
  final bool isDisplay;

  MathBuilder({this.isDisplay = false});

  @override
  Widget? visitElementAfter(md.Element element, TextStyle? preferredStyle) {
    final text = element.textContent;

    if (isDisplay) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 24),
        child: Center(
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: SelectableMath.tex(
              text,
              textStyle: (preferredStyle ?? const TextStyle()).copyWith(fontSize: 18),
              mathStyle: MathStyle.display,
              onErrorFallback: (error) {
                return Text(
                  'Error rendering math: ${error.message}\n$text',
                  style: const TextStyle(color: Colors.redAccent),
                );
              },
            ),
          ),
        ),
      );
    } else {
      return Builder(
        builder: (context) {
          // Prevent inline math from overflowing horizontally
          final maxWidth = MediaQuery.of(context).size.width * 0.75;
          return ConstrainedBox(
            constraints: BoxConstraints(maxWidth: maxWidth),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: SelectableMath.tex(
                text,
                textStyle: (preferredStyle ?? const TextStyle()).copyWith(fontSize: 18),
                mathStyle: MathStyle.text,
                onErrorFallback: (error) {
                  return Text(
                    text,
                    style: const TextStyle(color: Colors.redAccent),
                  );
                },
              ),
            ),
          );
        },
      );
    }
  }
}
