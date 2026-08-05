import 'package:flutter/material.dart';
import 'models.dart';
import 'widgets.dart';
import 'weather_widget.dart';

typedef WidgetBuilderFn = Widget Function(BuildContext context, PresentationNode node);

class PresentationRegistry {
  static final Map<String, WidgetBuilderFn> _registry = {
    'Heading': (context, node) => HeadingWidget(node: node as HeadingNode),
    'Paragraph': (context, node) => ParagraphWidget(node: node as ParagraphNode),
    'BulletList': (context, node) => BulletListWidget(node: node as BulletListNode),
    'NumberedList': (context, node) => NumberedListWidget(node: node as NumberedListNode),
    'ComparisonTable': (context, node) => ComparisonTableWidget(node: node as ComparisonTableNode),
    'CodeBlock': (context, node) => CodeBlockWidget(node: node as CodeBlockNode),
    'NewsCard': (context, node) => NewsCardWidget(node: node as NewsCardNode),
    'WeatherCard': (context, node) => WeatherCardWidget(node: node as WeatherCardNode),
    'Timeline': (context, node) => TimelineWidget(node: node as TimelineNode),
    'Accordion': (context, node) => AccordionWidget(node: node as AccordionNode),
    'ImageGallery': (context, node) => ImageGalleryWidget(node: node as ImageGalleryNode),
    // Additional widgets can be registered here
  };

  static void register(String type, WidgetBuilderFn builder) {
    _registry[type] = builder;
  }

  static Widget buildWidget(BuildContext context, PresentationNode node) {
    final builder = _registry[node.type];
    if (builder != null) {
      return builder(context, node);
    }
    // Fallback for unregistered or unknown nodes
    if (node is UnknownNode) {
      return UnknownNodeWidget(node: node);
    }
    return Container(
      padding: const EdgeInsets.all(8),
      color: Colors.orange.withOpacity(0.2),
      child: Text('Unregistered Component Type: ${node.type}'),
    );
  }
}
