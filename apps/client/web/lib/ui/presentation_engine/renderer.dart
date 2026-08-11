import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'models.dart';
import 'registry.dart';

class PresentationRenderer extends StatelessWidget {
  final List<PresentationNode> nodes;
  final String? fallbackMarkdown; // If legacy chat message

  const PresentationRenderer({
    super.key,
    required this.nodes,
    this.fallbackMarkdown,
  });

  @override
  Widget build(BuildContext context) {
    if (nodes.isEmpty && fallbackMarkdown != null) {
      // Legacy compatibility: Render raw Markdown for old messages
      return MarkdownBody(data: fallbackMarkdown!);
    }

    return SelectionArea(
      child: ListView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: nodes.length,
        itemBuilder: (context, index) {
          final node = nodes[index];
          return TweenAnimationBuilder<double>(
            key: ValueKey(node.id),
            tween: Tween<double>(begin: 0.0, end: 1.0),
            duration: const Duration(milliseconds: 280),
            curve: Curves.easeOutCubic,
            builder: (context, val, child) {
              return Transform.translate(
                offset: Offset(0, 12 * (1 - val)),
                child: Opacity(
                  opacity: val,
                  child: child,
                ),
              );
            },
            child: PresentationRegistry.buildWidget(context, node),
          );
        },
      ),
    );
  }
}

class StreamingParser {
  /// Parses JSON-lines strings progressively into PresentationNodes
  static List<PresentationNode> parseStream(String payload) {
    List<PresentationNode> parsedNodes = [];
    final lines = payload.split('\n');
    
    for (var line in lines) {
      line = line.trim();
      if (line.isEmpty) continue;
      
      try {
        final jsonMap = jsonDecode(line);
        final node = PresentationNode.fromJson(jsonMap);
        parsedNodes.add(node);
      } catch (e) {
        debugPrint('Failed to parse Presentation Node: $e\\nLine: $line');
      }
    }
    return parsedNodes;
  }
}
