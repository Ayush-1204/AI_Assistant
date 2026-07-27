import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:markdown/markdown.dart' as md;

class CalloutSyntax extends md.BlockSyntax {
  // Matches "Note:", "Tip:", etc at the start of a block.
  @override
  RegExp get pattern => RegExp(r'^(Note|Tip|Warning|Important|Success|Error|Information):\s*(.*)');

  @override
  md.Node? parse(md.BlockParser parser) {
    final match = pattern.firstMatch(parser.current.content);
    if (match == null) {
      parser.advance();
      return null;
    }

    final type = match[1]!;
    final firstLineContent = match[2]!;
    
    final lines = <String>[firstLineContent];
    parser.advance();

    // Consume subsequent lines that are not empty and not matching other block syntaxes
    while (!parser.isDone && !parser.current.content.trim().isEmpty) {
      lines.add(parser.current.content);
      parser.advance();
    }

    final content = lines.join('\n');
    
    final el = md.Element('callout', [md.Text(content)])
      ..attributes['type'] = type;
      
    return el;
  }
}

class CalloutBuilder extends MarkdownElementBuilder {
  @override
  Widget? visitElementAfter(md.Element element, TextStyle? preferredStyle) {
    final type = element.attributes['type'] ?? 'Note';
    final content = element.textContent;

    Color color;
    IconData icon;

    switch (type.toLowerCase()) {
      case 'warning':
        color = Colors.orange;
        icon = Icons.warning_amber_rounded;
        break;
      case 'error':
        color = Colors.redAccent;
        icon = Icons.error_outline_rounded;
        break;
      case 'success':
        color = Colors.green;
        icon = Icons.check_circle_outline_rounded;
        break;
      case 'tip':
      case 'important':
        color = Colors.blueAccent;
        icon = Icons.lightbulb_outline_rounded;
        break;
      case 'information':
      case 'note':
      default:
        color = Colors.blueGrey;
        icon = Icons.info_outline_rounded;
        break;
    }

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  type,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: color,
                    fontSize: 16,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  content,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.9),
                    fontSize: 15,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
