import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../markdown/ai_message_renderer.dart';
import 'models.dart';
import 'weather_widget.dart' show WeatherCardWidget;
import 'fullscreen_gallery.dart';
import 'registry.dart';
import '../../providers/auth_provider.dart';

import 'package:flutter/services.dart';
import 'package:flutter_highlighter/themes/atom-one-dark.dart';
import '../markdown/builders/selectable_highlight_view.dart';

void _openFullScreenGallery(
    BuildContext context, List<Map<String, String>> images, int initialIndex) {
  Navigator.of(context).push(PageRouteBuilder(
    pageBuilder: (context, animation, secondaryAnimation) =>
        FullScreenGallery(images: images, initialIndex: initialIndex),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      return FadeTransition(opacity: animation, child: child);
    },
  ));
}

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

class HoverZoomWrapper extends StatefulWidget {
  final Widget child;
  const HoverZoomWrapper({super.key, required this.child});

  @override
  State<HoverZoomWrapper> createState() => _HoverZoomWrapperState();
}

class _HoverZoomWrapperState extends State<HoverZoomWrapper> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: AnimatedScale(
        scale: _isHovered ? 1.05 : 1.0,
        duration: const Duration(milliseconds: 5000),
        curve: Curves.easeOut,
        child: widget.child,
      ),
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

class NumberedListWidget extends StatelessWidget {
  final NumberedListNode node;
  const NumberedListWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    int index = 1;
    final listMarkdown =
        node.items.map((item) => '${index++}. $item').join('\n');
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
    if (node.headers.isEmpty && node.rows.isEmpty) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16.0),
      child: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF151515), // Deep sleek background
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.4),
              blurRadius: 16,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        clipBehavior: Clip.antiAlias,
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minWidth: constraints.maxWidth,
                ),
                child: Table(
              defaultColumnWidth: const IntrinsicColumnWidth(),
              border: TableBorder(
                borderRadius: BorderRadius.circular(16),
                horizontalInside: BorderSide(
                    color: Colors.white.withValues(alpha: 0.05), width: 1),
                verticalInside: BorderSide(
                    color: Colors.white.withValues(alpha: 0.02), width: 1),
              ),
              defaultVerticalAlignment: TableCellVerticalAlignment.middle,
              children: [
                TableRow(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Theme.of(context).colorScheme.primary.withValues(alpha: 0.15),
                        Theme.of(context).colorScheme.primary.withValues(alpha: 0.03),
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                  ),
                  children: node.headers
                      .map((h) => Padding(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 24.0, vertical: 16.0),
                            child: Text(
                              h,
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Theme.of(context).colorScheme.primary,
                                fontSize: 15,
                                letterSpacing: 0.5,
                              ),
                            ),
                          ))
                      .toList(),
                ),
                ...node.rows.asMap().entries.map((entry) {
                  final idx = entry.key;
                  final row = entry.value;
                  return TableRow(
                    decoration: BoxDecoration(
                      color: idx % 2 == 0
                          ? Colors.transparent
                          : Colors.white.withValues(alpha: 0.02),
                    ),
                    children: row.asMap().entries.map((cellEntry) {
                      final cIdx = cellEntry.key;
                      final cell = cellEntry.value;
                      return Padding(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 24.0, vertical: 16.0),
                        child: Text(
                          cell.toString(),
                          style: TextStyle(
                            color: cIdx == 0
                                ? Colors.white.withValues(alpha: 0.95)
                                : Colors.white.withValues(alpha: 0.75),
                            fontWeight: cIdx == 0
                                ? FontWeight.w600
                                : FontWeight.normal,
                            fontSize: 14,
                            height: 1.5,
                          ),
                        ),
                      );
                    }).toList(),
                  );
                }),
              ],
            ),
          ),
        );
       },
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
    String language = node.language;
    if (language.isEmpty) language = 'plaintext';

    return Container(
      margin: const EdgeInsets.symmetric(vertical: 16.0),
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
                _CopyButton(text: node.code),
              ],
            ),
          ),
          // Code Content
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: SelectableHighlightView(
              node.code,
              padding: const EdgeInsets.all(16),
              language: language,
              theme: Map<String, TextStyle>.from(atomOneDarkTheme)
                ..['root'] = const TextStyle(
                  backgroundColor: Colors.transparent,
                  color: Color(0xffabb2bf),
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

class NewsCardWidget extends StatelessWidget {
  final NewsCardNode node;
  const NewsCardWidget({super.key, required this.node});

  /// Wraps any image URL through wsrv.nl proxy to bypass Flutter-web CORS restrictions
  String? _proxiedImage(String? url) {
    if (url == null || url.isEmpty) return null;

    // Clean Wikipedia/Wikimedia URLs to avoid wsrv.nl cache corruption or encoding bugs
    String cleanUrl = url;
    if (cleanUrl.contains('?utm_') || cleanUrl.contains('&utm_')) {
      cleanUrl = cleanUrl.split('?').first;
    }

    final encoded = Uri.encodeComponent(cleanUrl);
    return 'https://wsrv.nl/?url=$encoded&w=800&h=400&fit=cover&output=jpg';
  }

  String _formatDate(String? dateStr) {
    if (dateStr == null || dateStr.isEmpty) return '';
    try {
      final dt = DateTime.parse(dateStr).toLocal();
      // Using a simple format like "MMM d, yyyy h:mm a" without adding intl dependency logic
      final months = [
        'Jan',
        'Feb',
        'Mar',
        'Apr',
        'May',
        'Jun',
        'Jul',
        'Aug',
        'Sep',
        'Oct',
        'Nov',
        'Dec'
      ];
      final month = months[dt.month - 1];
      final hour = dt.hour % 12 == 0 ? 12 : dt.hour % 12;
      final amPm = dt.hour >= 12 ? 'PM' : 'AM';
      final minute = dt.minute.toString().padLeft(2, '0');
      return '$month ${dt.day}, ${dt.year} $hour:$minute $amPm';
    } catch (e) {
      return dateStr;
    }
  }

  List<String> get _images {
    final List<String> urls = [];
    if (node.imageUrl != null && node.imageUrl!.isNotEmpty) {
      urls.add(node.imageUrl!);
    }
    for (final url in node.imageUrls) {
      if (!urls.contains(url)) urls.add(url);
    }
    return urls.map((u) => _proxiedImage(u)).whereType<String>().toList();
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
    final images = _images;
    final mappedImages =
        images.map((url) => {'url': url, 'alt': node.title}).toList();

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
                if (images.length == 1)
                  GestureDetector(
                    onTap: () =>
                        _openFullScreenGallery(context, mappedImages, 0),
                    child: ClipRRect(
                      borderRadius:
                          const BorderRadius.vertical(top: Radius.circular(14)),
                      child: HoverZoomWrapper(
                        child: Image.network(
                          images.first,
                          height: 160,
                          width: double.infinity,
                          fit: BoxFit.cover,
                          errorBuilder: (_, __, ___) => const SizedBox.shrink(),
                          loadingBuilder: (_, child, progress) {
                            if (progress == null) return child;
                            return Container(
                              height: 160,
                              color: theme.colorScheme.surfaceContainer,
                              child: const Center(
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2)),
                            );
                          },
                        ),
                      ),
                    ),
                  )
                else if (images.length > 1)
                  SizedBox(
                    height: 180,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 14),
                      itemCount: images.length,
                      separatorBuilder: (context, index) =>
                          const SizedBox(width: 12),
                      itemBuilder: (context, index) {
                        return GestureDetector(
                          onTap: () => _openFullScreenGallery(
                              context, mappedImages, index),
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(10),
                            child: HoverZoomWrapper(
                              child: Image.network(
                                images[index],
                                height: 152,
                                width: 240,
                                fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) =>
                                    const SizedBox.shrink(),
                                loadingBuilder: (_, child, progress) {
                                  if (progress == null) return child;
                                  return Container(
                                    height: 152,
                                    width: 240,
                                    color: theme.colorScheme.surfaceContainer,
                                    child: const Center(
                                        child: CircularProgressIndicator(
                                            strokeWidth: 2)),
                                  );
                                },
                              ),
                            ),
                          ),
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
                      if (node.category != null &&
                          node.category!.isNotEmpty) ...[
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 3),
                          decoration: BoxDecoration(
                            color: theme.colorScheme.primary
                                .withValues(alpha: 0.12),
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
                          color: theme.colorScheme.onSurface
                              .withValues(alpha: 0.65),
                          height: 1.5,
                        ),
                      ),
                      const SizedBox(height: 14),

                      // Divider
                      Divider(
                          height: 1,
                          color: theme.dividerColor.withValues(alpha: 0.2)),
                      const SizedBox(height: 10),

                      // Footer: source + date + open icon
                      Row(
                        children: [
                          Icon(Icons.article_outlined,
                              size: 14, color: theme.colorScheme.primary),
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
                          if (node.publishedAt != null &&
                              node.publishedAt!.isNotEmpty) ...[
                            Text(
                              _formatDate(node.publishedAt),
                              style: TextStyle(
                                fontSize: 11,
                                color: theme.colorScheme.onSurface
                                    .withValues(alpha: 0.4),
                              ),
                            ),
                            const SizedBox(width: 8),
                          ],
                          if (hasUrl)
                            Icon(Icons.open_in_new_rounded,
                                size: 14,
                                color: theme.colorScheme.primary
                                    .withValues(alpha: 0.7)),
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
                      decoration: const BoxDecoration(
                          color: Colors.blue, shape: BoxShape.circle),
                    ),
                    Container(
                        width: 2,
                        height: 50,
                        color: Colors.blue.withValues(alpha: 0.3)),
                  ],
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(event['time'] ?? '',
                          style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: Colors.grey)),
                      const SizedBox(height: 4),
                      Text(event['title'] ?? '',
                          style: const TextStyle(
                              fontSize: 16, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
                      Text(event['description'] ?? '',
                          style: const TextStyle(fontSize: 14)),
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
        title: Text(node.title,
            style: const TextStyle(fontWeight: FontWeight.bold)),
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

class ImageGalleryWidget extends StatelessWidget {
  final ImageGalleryNode node;
  const ImageGalleryWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    if (node.images.isEmpty) return const SizedBox.shrink();
    if (node.layout == 'bento' && node.images.length >= 3) {
      return _BentoGalleryWidget(images: node.images);
    }
    if (node.images.length == 1) {
      return _SingleImageGalleryWidget(image: node.images.first);
    }
    return _CarouselGalleryWidget(images: node.images);
  }
}

class _SingleImageGalleryWidget extends StatelessWidget {
  final Map<String, String> image;
  const _SingleImageGalleryWidget({required this.image});

  String? _proxiedImage(String? url) {
    if (url == null || url.isEmpty) return null;

    // Clean Wikipedia/Wikimedia URLs to avoid wsrv.nl cache corruption or encoding bugs
    String cleanUrl = url;
    if (cleanUrl.contains('?utm_') || cleanUrl.contains('&utm_')) {
      cleanUrl = cleanUrl.split('?').first;
    }

    final encoded = Uri.encodeComponent(cleanUrl);
    // Remove strict crop (fit=cover) and height limits so it scales proportionally
    return 'https://wsrv.nl/?url=$encoded&w=800&output=jpg';
  }

  @override
  Widget build(BuildContext context) {
    final url = _proxiedImage(image['url']);
    if (url == null) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16.0),
      child: GestureDetector(
        onTap: () => _openFullScreenGallery(context, [image], 0),
        child: ConstrainedBox(
          constraints:
              const BoxConstraints(maxHeight: 400, maxWidth: double.infinity),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: HoverZoomWrapper(
              child: Image.network(
                url,
                fit: BoxFit.contain, // Prevents overly cropping
                errorBuilder: (_, __, ___) => Container(
                  height: 200,
                  color: Theme.of(context).colorScheme.surfaceContainer,
                  child: const Center(
                      child: Icon(Icons.broken_image, color: Colors.grey)),
                ),
                loadingBuilder: (_, child, progress) {
                  if (progress == null) return child;
                  return Container(
                    height: 200,
                    color: Theme.of(context).colorScheme.surfaceContainer,
                    child: const Center(
                        child: CircularProgressIndicator(strokeWidth: 2)),
                  );
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _CarouselGalleryWidget extends StatelessWidget {
  final List<Map<String, String>> images;
  const _CarouselGalleryWidget({required this.images});

  String? _proxiedImage(String? url) {
    if (url == null || url.isEmpty) return null;

    // Clean Wikipedia/Wikimedia URLs to avoid wsrv.nl cache corruption or encoding bugs
    String cleanUrl = url;
    if (cleanUrl.contains('?utm_') || cleanUrl.contains('&utm_')) {
      cleanUrl = cleanUrl.split('?').first;
    }

    final encoded = Uri.encodeComponent(cleanUrl);
    return 'https://wsrv.nl/?url=$encoded&w=500&h=500&fit=cover&output=jpg';
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16.0),
      child: LayoutBuilder(
        builder: (context, constraints) {
          const gap = 12.0;
          // Calculate item width to fit exactly 3 items perfectly in the available constraints
          final itemWidth = (constraints.maxWidth - (gap * 2)) / 3.0;
          // Keep the images perfectly square based on the calculated dynamic width
          final itemHeight = itemWidth;

          return SizedBox(
            height: itemHeight,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: images.length,
              separatorBuilder: (context, index) => const SizedBox(width: gap),
              itemBuilder: (context, index) {
                final img = images[index];
                final url = _proxiedImage(img['url']);
                if (url == null) return const SizedBox.shrink();

                return GestureDetector(
                  onTap: () => _openFullScreenGallery(context, images, index),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: HoverZoomWrapper(
                      child: Image.network(
                        url,
                        height: itemHeight,
                        width: itemWidth,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => Container(
                          width: itemWidth,
                          height: itemHeight,
                          color: Theme.of(context).colorScheme.surfaceContainer,
                          child: const Center(
                              child:
                                  Icon(Icons.broken_image, color: Colors.grey)),
                        ),
                        loadingBuilder: (_, child, progress) {
                          if (progress == null) return child;
                          return Container(
                            height: itemHeight,
                            width: itemWidth,
                            color:
                                Theme.of(context).colorScheme.surfaceContainer,
                            child: const Center(
                                child:
                                    CircularProgressIndicator(strokeWidth: 2)),
                          );
                        },
                      ),
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}

class _BentoGalleryWidget extends StatelessWidget {
  final List<Map<String, String>> images;
  const _BentoGalleryWidget({required this.images});

  String? _proxiedImage(String? url, {int w = 800, int h = 600}) {
    if (url == null || url.isEmpty) return null;

    String cleanUrl = url;
    if (cleanUrl.contains('?utm_') || cleanUrl.contains('&utm_')) {
      cleanUrl = cleanUrl.split('?').first;
    }

    final encoded = Uri.encodeComponent(cleanUrl);
    return 'https://wsrv.nl/?url=$encoded&w=$w&h=$h&fit=cover&output=jpg';
  }

  Widget _buildImage(BuildContext context, int index, int width, int height) {
    final img = images[index];
    final url = _proxiedImage(img['url'], w: width, h: height);
    if (url == null) return const SizedBox.shrink();

    return GestureDetector(
      onTap: () => _openFullScreenGallery(context, images, index),
      child: HoverZoomWrapper(
        child: Image.network(
          url,
          fit: BoxFit.cover,
          width: double.infinity,
          height: double.infinity,
          errorBuilder: (_, __, ___) => Container(
            color: Theme.of(context).colorScheme.surfaceContainer,
            child: const Center(
                child: Icon(Icons.broken_image, color: Colors.grey)),
          ),
          loadingBuilder: (_, child, progress) {
            if (progress == null) return child;
            return Container(
              color: Theme.of(context).colorScheme.surfaceContainer,
              child: const Center(
                  child: CircularProgressIndicator(strokeWidth: 2)),
            );
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final remainingCount = images.length - 3;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16.0),
      child: SizedBox(
        height: 400,
        child: Row(
          children: [
            Expanded(
              flex: 2,
              child: ClipRRect(
                borderRadius:
                    const BorderRadius.horizontal(left: Radius.circular(12)),
                child: _buildImage(context, 0, 800, 700),
              ),
            ),
            const SizedBox(width: 4),
            Expanded(
              flex: 1,
              child: Column(
                children: [
                  Expanded(
                    child: ClipRRect(
                      borderRadius: const BorderRadius.only(
                          topRight: Radius.circular(12)),
                      child: _buildImage(context, 1, 400, 350),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Expanded(
                    child: ClipRRect(
                      borderRadius: const BorderRadius.only(
                          bottomRight: Radius.circular(12)),
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          _buildImage(context, 2, 400, 350),
                          if (remainingCount > 0)
                            Positioned(
                              bottom: 8,
                              right: 8,
                              child: GestureDetector(
                                onTap: () =>
                                    _openFullScreenGallery(context, images, 2),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: Colors.black54,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    '+$remainingCount',
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 20,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class HeaderWidget extends StatelessWidget {
  final HeaderNode node;
  const HeaderWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 24.0, horizontal: 16.0),
      margin: const EdgeInsets.symmetric(vertical: 16.0),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            theme.colorScheme.primaryContainer,
            theme.colorScheme.primary.withValues(alpha: 0.1)
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border:
            Border.all(color: theme.colorScheme.primary.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (node.userName.isNotEmpty)
            Text(
              'Hi ${node.userName}, here is your dashboard',
              style: theme.textTheme.labelLarge?.copyWith(
                color: theme.colorScheme.primary,
                letterSpacing: 1.2,
                fontWeight: FontWeight.w600,
              ),
            ),
          const SizedBox(height: 8),
          Text(
            node.title,
            style: theme.textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: theme.colorScheme.onSurface,
            ),
          ),
        ],
      ),
    );
  }
}

class CardWidget extends StatelessWidget {
  final CardNode node;
  const CardWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: theme.dividerColor.withValues(alpha: 0.2)),
      ),
      color: theme.colorScheme.surface,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min, // shrink-wrap contents
          children: [
            Text(
              node.title,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              node.description,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withValues(alpha: 0.7),
                height: 1.4,
              ),
            ),
            if (node.tags.isNotEmpty) ...[
              const SizedBox(height: 16),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: node.tags
                    .map((tag) => Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: theme.colorScheme.secondaryContainer
                                .withValues(alpha: 0.5),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Text(
                            tag,
                            style: TextStyle(
                              fontSize: 11,
                              color: theme.colorScheme.onSecondaryContainer,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ))
                    .toList(),
              ),
            ]
          ],
        ),
      ),
    );
  }
}

class GridWidget extends StatelessWidget {
  final GridNode node;
  const GridWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16.0),
      child: LayoutBuilder(
        builder: (context, constraints) {
          // Responsive layout: fallback to 1 column if too narrow
          final isNarrow = constraints.maxWidth < 600;
          final columns = isNarrow ? 1 : node.columns;
          final spacing = 12.0;

          return Wrap(
            spacing: spacing,
            runSpacing: spacing,
            children: node.items.map((item) {
              final childWidth =
                  (constraints.maxWidth - (spacing * (columns - 1))) / columns;
              return SizedBox(
                width: columns == 1 ? constraints.maxWidth : childWidth,
                child: PresentationRegistry.buildWidget(context, item),
              );
            }).toList(),
          );
        },
      ),
    );
  }
}

class SectionWidget extends StatelessWidget {
  final SectionNode node;
  const SectionWidget({super.key, required this.node});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 20.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 4,
                height: 24,
                decoration: BoxDecoration(
                  color: theme.colorScheme.primary,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  node.title,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          AiMessageRenderer(
            text: node.content,
            wrapInSelectionArea: false,
          ),
        ],
      ),
    );
  }
}

class EventCardWidget extends ConsumerWidget {
  final EventCardNode node;
  const EventCardWidget({super.key, required this.node});

  String _formatDate(String isoString) {
    if (isoString.isEmpty) return '';
    try {
      final dt = DateTime.parse(isoString).toLocal();
      return DateFormat('MMM d, yyyy • h:mm a').format(dt);
    } catch (_) {
      return isoString;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1E1E).withOpacity(0.9),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.4),
            blurRadius: 10,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.indigoAccent.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.event,
                    color: Colors.indigoAccent, size: 24),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      node.title.isEmpty ? 'Untitled Event' : node.title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${_formatDate(node.startTime)} - ${_formatDate(node.endTime).split('•').last.trim()}',
                      style: const TextStyle(
                        fontSize: 13,
                        color: Colors.white60,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              if (node.eventId != null && node.eventId!.isNotEmpty) ...[
                IconButton(
                  onPressed: () {
                    // TODO: Implement Edit logic (e.g. open rich edit dialog)
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                            content:
                                Text('Edit event not fully hooked up yet.')),
                      );
                    }
                  },
                  icon: const Icon(Icons.edit_outlined,
                      color: Colors.blueAccent, size: 20),
                  tooltip: 'Edit Event',
                ),
                IconButton(
                  onPressed: () async {
                    try {
                      await ref
                          .read(apiClientProvider)
                          .deleteCalendarEvent(node.eventId!);
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                              content: Text('Event deleted successfully.')),
                        );
                      }
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                              content: Text('Failed to delete event.')),
                        );
                      }
                    }
                  },
                  icon: const Icon(Icons.delete_outline,
                      color: Colors.redAccent, size: 20),
                  tooltip: 'Delete Event',
                ),
              ],
              const SizedBox(width: 8),
              if (node.link != null && node.link!.isNotEmpty)
                ElevatedButton.icon(
                  onPressed: () async {
                    final url = Uri.parse(node.link!);
                    if (await canLaunchUrl(url)) {
                      await launchUrl(url);
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10)),
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 10),
                  ),
                  icon: const Icon(Icons.open_in_new, size: 16),
                  label: const Text('View in Calendar',
                      style:
                          TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
