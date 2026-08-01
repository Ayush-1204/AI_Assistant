import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../markdown/ai_message_renderer.dart';
import 'models.dart';
import 'weather_widget.dart' show WeatherCardWidget;

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

  /// Wraps any image URL through wsrv.nl proxy to bypass Flutter-web CORS restrictions
  String? _proxiedImage(String? url) {
    if (url == null || url.isEmpty) return null;
    final encoded = Uri.encodeComponent(url);
    return 'https://wsrv.nl/?url=$encoded&w=800&h=400&fit=cover&output=jpg';
  }

  String? get _imageUrl {
    if (node.imageUrl != null && node.imageUrl!.isNotEmpty) return _proxiedImage(node.imageUrl);
    if (node.imageUrls.isNotEmpty) return _proxiedImage(node.imageUrls.first);
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
      padding: const EdgeInsets.symmetric(vertical: 10.0),
      child: Material(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(14),
        clipBehavior: Clip.antiAlias,
        elevation: 0,
        child: InkWell(
          onTap: hasUrl ? () => _openUrl(context) : null,
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: theme.dividerColor.withValues(alpha: 0.25),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // --- Top image banner ---
                if (imageUrl != null)
                  ClipRRect(
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(14)),
                    child: Image.network(
                      imageUrl,
                      height: 160,
                      width: double.infinity,
                      fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                      loadingBuilder: (_, child, progress) {
                        if (progress == null) return child;
                        return Container(
                          height: 160,
                          color: theme.colorScheme.surfaceContainer,
                          child: const Center(child: CircularProgressIndicator(strokeWidth: 2)),
                        );
                      },
                    ),
                  ),

                // --- Card body ---
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Category chip
                      if (node.category != null && node.category!.isNotEmpty) ...[
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                          decoration: BoxDecoration(
                            color: theme.colorScheme.primary.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            node.category!.toUpperCase(),
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w800,
                              color: theme.colorScheme.primary,
                              letterSpacing: 0.8,
                            ),
                          ),
                        ),
                        const SizedBox(height: 10),
                      ],

                      // Title
                      Text(
                        node.title,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          height: 1.4,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 8),

                      // Summary
                      Text(
                        node.summary,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.colorScheme.onSurface.withValues(alpha: 0.65),
                          height: 1.5,
                        ),
                        maxLines: 4,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 14),

                      // Divider
                      Divider(height: 1, color: theme.dividerColor.withValues(alpha: 0.2)),
                      const SizedBox(height: 10),

                      // Footer: source + date + open icon
                      Row(
                        children: [
                          Icon(Icons.article_outlined, size: 14, color: theme.colorScheme.primary),
                          const SizedBox(width: 5),
                          Expanded(
                            child: Text(
                              node.source,
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                                color: theme.colorScheme.primary,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          if (node.publishedAt != null && node.publishedAt!.isNotEmpty) ...[
                            Text(
                              node.publishedAt!,
                              style: TextStyle(
                                fontSize: 11,
                                color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
                              ),
                            ),
                            const SizedBox(width: 8),
                          ],
                          if (hasUrl)
                            Icon(Icons.open_in_new_rounded, size: 14,
                                color: theme.colorScheme.primary.withValues(alpha: 0.7)),
                        ],
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
        side: BorderSide(color: Colors.grey.withValues(alpha: 0.3)),
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
