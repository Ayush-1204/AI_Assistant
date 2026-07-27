import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../markdown/ai_message_renderer.dart';
import 'models.dart';

class UnknownNodeWidget extends StatelessWidget {
  final UnknownNode node;
  const UnknownNodeWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(8),
      color: Colors.red.withValues(alpha: 0.1),
      child: Text('Unknown Component: ${node.rawJson['type']}'),
    );
  }
}

class HeadingWidget extends StatelessWidget {
  final HeadingNode node;
  const HeadingWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    double fontSize = 24.0;
    FontWeight weight = FontWeight.bold;
    if (node.level == 1) {
      fontSize = 32.0;
      weight = FontWeight.w900;
    } else if (node.level == 3) {
      fontSize = 20.0;
      weight = FontWeight.w600;
    }

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: AiMessageRenderer(
        text: '${'#' * node.level} ${node.text}',
        wrapInSelectionArea: false,
      ),
    );
  }
}

class ParagraphWidget extends StatelessWidget {
  final ParagraphNode node;
  const ParagraphWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 0.0),
      child: AiMessageRenderer(
        text: node.text,
        wrapInSelectionArea: false,
      ),
    );
  }
}

class BulletListWidget extends StatelessWidget {
  final BulletListNode node;
  const BulletListWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    final listMarkdown = node.items.map((item) => '* $item').join('\n');
    return Padding(
      padding: const EdgeInsets.only(bottom: 0.0),
      child: AiMessageRenderer(
        text: listMarkdown,
        wrapInSelectionArea: false,
      ),
    );
  }
}

class ComparisonTableWidget extends StatelessWidget {
  final ComparisonTableNode node;
  const ComparisonTableWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16.0),
        child: DataTable(
          headingRowColor: WidgetStateProperty.all(Colors.grey.withValues(alpha: 0.1)),
          border: TableBorder.all(color: Colors.grey.withValues(alpha: 0.3)),
          columns: node.headers.map((h) => DataColumn(label: Text(h, style: const TextStyle(fontWeight: FontWeight.bold)))).toList(),
          rows: node.rows.map((row) {
            return DataRow(
              cells: row.map((cell) => DataCell(Text(cell))).toList(),
            );
          }).toList(),
        ),
      ),
    );
  }
}

class CodeBlockWidget extends StatelessWidget {
  final CodeBlockNode node;
  const CodeBlockWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    // For simplicity, reusing Markdown formatting for the code block
    // A robust app would use flutter_highlighter
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 16.0),
      decoration: BoxDecoration(
        color: Colors.black87,
        borderRadius: BorderRadius.circular(8),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(node.language.toUpperCase(), style: const TextStyle(color: Colors.white54, fontSize: 12, fontWeight: FontWeight.bold)),
              const Icon(Icons.copy, color: Colors.white54, size: 16),
            ],
          ),
          const SizedBox(height: 8),
          SelectableText(
            node.code,
            style: const TextStyle(fontFamily: 'monospace', color: Colors.greenAccent, fontSize: 14),
          ),
        ],
      ),
    );
  }
}

class NewsCardWidget extends StatelessWidget {
  final NewsCardNode node;
  const NewsCardWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      margin: const EdgeInsets.symmetric(vertical: 12.0),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (node.imageUrl != null && node.imageUrl!.isNotEmpty)
            ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
              child: Image.network(
                node.imageUrl!,
                height: 150,
                width: double.infinity,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const SizedBox.shrink(),
              ),
            ),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(node.title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                Text(node.summary, style: const TextStyle(fontSize: 14, color: Colors.grey)),
                const SizedBox(height: 12),
                Row(
                  children: [
                    const Icon(Icons.source, size: 14, color: Colors.blueAccent),
                    const SizedBox(width: 4),
                    Text(node.source, style: const TextStyle(fontSize: 12, color: Colors.blueAccent, fontWeight: FontWeight.w600)),
                  ],
                ),
              ],
            ),
          )
        ],
      ),
    );
  }
}

class TimelineWidget extends StatelessWidget {
  final TimelineNode node;
  const TimelineWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: node.events.map((event) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 16.0),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Column(
                  children: [
                    Container(
                      width: 12,
                      height: 12,
                      decoration: const BoxDecoration(color: Colors.blue, shape: BoxShape.circle),
                    ),
                    Container(width: 2, height: 50, color: Colors.blue.withValues(alpha: 0.3)),
                  ],
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(event['time'] ?? '', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.grey)),
                      const SizedBox(height: 4),
                      Text(event['title'] ?? '', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
                      Text(event['description'] ?? '', style: const TextStyle(fontSize: 14)),
                    ],
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}

class WeatherCardWidget extends StatelessWidget {
  final WeatherCardNode node;
  const WeatherCardWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          gradient: const LinearGradient(
            colors: [Color(0xFF2C3E50), Color(0xFF3498DB)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  node.location,
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                const Icon(Icons.cloud, color: Colors.white, size: 32),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              '${node.temperatureC.toStringAsFixed(1)}°C',
              style: const TextStyle(fontSize: 48, fontWeight: FontWeight.w900, color: Colors.white),
            ),
            const SizedBox(height: 8),
            Text(
              node.condition,
              style: const TextStyle(fontSize: 18, color: Colors.white70),
            ),
          ],
        ),
      ),
    );
  }
}
