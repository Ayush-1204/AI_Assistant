import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:url_launcher/url_launcher.dart';
import '../markdown/ai_message_renderer.dart';
import 'models.dart';
import 'weather_widget.dart';

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

  String? get _imageUrl {
    if (node.imageUrl != null && node.imageUrl!.isNotEmpty) return node.imageUrl;
    if (node.imageUrls.isNotEmpty) return node.imageUrls.first;
    return null;
  }

  void _openUrl(BuildContext context) async {
    final rawUrl = node.url;
    if (rawUrl == null || rawUrl.isEmpty) return;
    try {
      final uri = Uri.parse(rawUrl);
      // ignore: deprecated_member_use
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not open article')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasUrl = node.url != null && node.url!.isNotEmpty;
    final imageUrl = _imageUrl;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Material(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: hasUrl ? () => _openUrl(context) : null,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            decoration: BoxDecoration(
              border: Border.all(
                color: theme.dividerColor.withOpacity(0.3),
                width: 1,
              ),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // --- Text Content (left) ---
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Category chip
                        if (node.category != null && node.category!.isNotEmpty) ...[
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: theme.colorScheme.primary.withOpacity(0.12),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              node.category!.toUpperCase(),
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: theme.colorScheme.primary,
                                letterSpacing: 0.5,
                              ),
                            ),
                          ),
                          const SizedBox(height: 6),
                        ],
                        // Title
                        Text(
                          node.title,
                          style: theme.textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            height: 1.35,
                          ),
                          maxLines: 3,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 6),
                        // Summary
                        Text(
                          node.summary,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurface.withOpacity(0.65),
                            height: 1.4,
                          ),
                          maxLines: 3,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 10),
                        // Source + date + arrow row
                        Row(
                          children: [
                            Icon(Icons.article_outlined, size: 12, color: theme.colorScheme.primary),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(
                                node.source,
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: theme.colorScheme.primary,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            if (node.publishedAt != null && node.publishedAt!.isNotEmpty) ...[
                              const SizedBox(width: 8),
                              Text(
                                node.publishedAt!,
                                style: TextStyle(
                                  fontSize: 11,
                                  color: theme.colorScheme.onSurface.withOpacity(0.45),
                                ),
                              ),
                            ],
                            if (hasUrl) ...[
                              const SizedBox(width: 6),
                              Icon(Icons.open_in_new, size: 12, color: theme.colorScheme.primary.withOpacity(0.7)),
                            ],
                          ],
                        ),
                      ],
                    ),
                  ),
                  // --- Thumbnail (right) ---
                  if (imageUrl != null) ...[
                    const SizedBox(width: 12),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.network(
                        imageUrl,
                        width: 80,
                        height: 80,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                        loadingBuilder: (_, child, loadingProgress) {
                          if (loadingProgress == null) return child;
                          return Container(
                            width: 80,
                            height: 80,
                            decoration: BoxDecoration(
                              color: theme.colorScheme.surfaceContainer,
                              borderRadius: BorderRadius.circular(8),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
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

class AccordionWidget extends StatelessWidget {
  final AccordionNode node;
  const AccordionWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      margin: const EdgeInsets.symmetric(vertical: 8.0),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: Colors.grey.withOpacity(0.3)),
      ),
      child: ExpansionTile(
        title: Text(node.title, style: const TextStyle(fontWeight: FontWeight.bold)),
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16.0, 0.0, 16.0, 16.0),
            child: AiMessageRenderer(
              text: node.content,
              wrapInSelectionArea: false,
            ),
          ),
        ],
      ),
    );
  }
}
