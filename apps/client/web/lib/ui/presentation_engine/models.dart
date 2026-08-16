abstract class PresentationNode {
  final String id;
  final String type;

  PresentationNode({required this.id, required this.type});

  factory PresentationNode.fromJson(Map<String, dynamic> json) {
    final type = (json['type'] as String?)?.toLowerCase();
    final id = json['id'] as String? ?? 'unknown';

    switch (type) {
      case 'heading':
        return HeadingNode.fromJson(json);
      case 'paragraph':
        return ParagraphNode.fromJson(json);
      case 'bulletlist':
        return BulletListNode.fromJson(json);
      case 'numberedlist':
        return NumberedListNode.fromJson(json);
      case 'newscard':
        return NewsCardNode.fromJson(json);
      case 'weathercard':
        return WeatherCardNode.fromJson(json);
      case 'table':
      case 'comparisontable':
        return ComparisonTableNode.fromJson(json);
      case 'codeblock':
        return CodeBlockNode.fromJson(json);
      case 'imagegallery':
        return ImageGalleryNode.fromJson(json);
      case 'timeline':
        return TimelineNode.fromJson(json);
      case 'accordion':
        return AccordionNode.fromJson(json);
      case 'eventcard':
        return EventCardNode.fromJson(json);
      case 'header':
        return HeaderNode.fromJson(json);
      case 'grid':
        return GridNode.fromJson(json);
      case 'card':
        return CardNode.fromJson(json);
      case 'section':
        return SectionNode.fromJson(json);
      default:
        return UnknownNode(id: id, rawJson: json);
    }
  }
}

class UnknownNode extends PresentationNode {
  final Map<String, dynamic> rawJson;
  UnknownNode({required super.id, required this.rawJson}) : super(type: 'Unknown');
}

class HeadingNode extends PresentationNode {
  final String text;
  final int level;

  HeadingNode({required super.id, required this.text, this.level = 1}) : super(type: 'Heading');

  factory HeadingNode.fromJson(Map<String, dynamic> json) {
    return HeadingNode(
      id: json['id'] ?? '',
      text: json['text'] ?? '',
      level: json['level'] ?? 1,
    );
  }
}

class ParagraphNode extends PresentationNode {
  final String text;

  ParagraphNode({required super.id, required this.text}) : super(type: 'Paragraph');

  factory ParagraphNode.fromJson(Map<String, dynamic> json) {
    return ParagraphNode(
      id: json['id'] ?? '',
      text: json['text'] ?? '',
    );
  }
}

class BulletListNode extends PresentationNode {
  final List<String> items;

  BulletListNode({required super.id, required this.items}) : super(type: 'BulletList');

  factory BulletListNode.fromJson(Map<String, dynamic> json) {
    return BulletListNode(
      id: json['id'] ?? '',
      items: (json['items'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
    );
  }
}

class NumberedListNode extends PresentationNode {
  final List<String> items;

  NumberedListNode({required super.id, required this.items}) : super(type: 'NumberedList');

  factory NumberedListNode.fromJson(Map<String, dynamic> json) {
    return NumberedListNode(
      id: json['id'] ?? '',
      items: (json['items'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
    );
  }
}

class NewsCardNode extends PresentationNode {
  final String title;
  final String summary;
  final String source;
  final String? url;
  final String? imageUrl;
  final List<String> imageUrls;
  final String? publishedAt;
  final String? category;

  NewsCardNode({
    required super.id,
    required this.title,
    required this.summary,
    required this.source,
    this.url,
    this.imageUrl,
    this.imageUrls = const [],
    this.publishedAt,
    this.category,
  }) : super(type: 'NewsCard');

  factory NewsCardNode.fromJson(Map<String, dynamic> json) {
    return NewsCardNode(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      summary: json['summary'] ?? '',
      source: json['source'] ?? '',
      url: json['url'],
      imageUrl: json['imageUrl'],
      imageUrls: (json['imageUrls'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      publishedAt: json['publishedAt'],
      category: json['category'],
    );
  }
}

class WeatherCardNode extends PresentationNode {
  final String location;
  final double temperatureC;
  final String condition;
  final List<dynamic> forecast;

  WeatherCardNode({
    required super.id,
    required this.location,
    required this.temperatureC,
    required this.condition,
    this.forecast = const [],
  }) : super(type: 'WeatherCard');

  factory WeatherCardNode.fromJson(Map<String, dynamic> json) {
    double parseTemp(dynamic val) {
      if (val == null) return 0.0;
      if (val is num) return val.toDouble();
      if (val is String) {
        final parsed = double.tryParse(val);
        if (parsed != null) return parsed;
      }
      return 0.0;
    }

    return WeatherCardNode(
      id: json['id'] ?? '',
      location: json['location'] ?? '',
      temperatureC: parseTemp(json['temperature_c']),
      condition: json['condition'] ?? '',
      forecast: json['forecast'] ?? [],
    );
  }
}

class ComparisonTableNode extends PresentationNode {
  final List<String> headers;
  final List<List<String>> rows;

  ComparisonTableNode({required super.id, required this.headers, required this.rows})
      : super(type: 'ComparisonTable');

  factory ComparisonTableNode.fromJson(Map<String, dynamic> json) {
    final rawHeaders = json['headers'] as List<dynamic>? ?? [];
    final rawRows = json['rows'] as List<dynamic>? ?? [];

    return ComparisonTableNode(
      id: json['id'] ?? '',
      headers: rawHeaders.map((e) => e.toString()).toList(),
      rows: rawRows.map((r) => (r as List<dynamic>).map((e) => e.toString()).toList()).toList(),
    );
  }
}

class CodeBlockNode extends PresentationNode {
  final String language;
  final String code;

  CodeBlockNode({required super.id, required this.language, required this.code})
      : super(type: 'CodeBlock');

  factory CodeBlockNode.fromJson(Map<String, dynamic> json) {
    return CodeBlockNode(
      id: json['id'] ?? '',
      language: json['language'] ?? 'text',
      code: json['code'] ?? '',
    );
  }
}

class ImageGalleryNode extends PresentationNode {
  final String layout;
  final List<Map<String, String>> images;

  ImageGalleryNode({required super.id, this.layout = 'carousel', required this.images}) : super(type: 'ImageGallery');

  factory ImageGalleryNode.fromJson(Map<String, dynamic> json) {
    final rawImages = json['images'] as List<dynamic>? ?? [];
    return ImageGalleryNode(
      id: json['id'] ?? '',
      layout: json['layout'] as String? ?? 'carousel',
      images: rawImages.map((e) {
        final map = e as Map<String, dynamic>;
        return {
          'url': map['url']?.toString() ?? '',
          'alt': map['alt']?.toString() ?? '',
        };
      }).toList(),
    );
  }
}

class TimelineNode extends PresentationNode {
  final List<Map<String, String>> events;

  TimelineNode({required super.id, required this.events}) : super(type: 'Timeline');

  factory TimelineNode.fromJson(Map<String, dynamic> json) {
    final rawEvents = json['events'] as List<dynamic>? ?? [];
    return TimelineNode(
      id: json['id'] ?? '',
      events: rawEvents.map((e) {
        final map = e as Map<String, dynamic>;
        return {
          'time': map['time']?.toString() ?? '',
          'title': map['title']?.toString() ?? '',
          'description': map['description']?.toString() ?? '',
        };
      }).toList(),
    );
  }
}

class AccordionNode extends PresentationNode {
  final String title;
  final String content;

  AccordionNode({required super.id, required this.title, required this.content})
      : super(type: 'Accordion');

  factory AccordionNode.fromJson(Map<String, dynamic> json) {
    return AccordionNode(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      content: json['content'] ?? '',
    );
  }
}

class HeaderNode extends PresentationNode {
  final String title;
  final String userName;

  HeaderNode({required super.id, required this.title, required this.userName})
      : super(type: 'header');

  factory HeaderNode.fromJson(Map<String, dynamic> json) {
    final content = json['content'] as Map<String, dynamic>? ?? {};
    return HeaderNode(
      id: json['id'] ?? '',
      title: content['title'] ?? json['title'] ?? '',
      userName: content['user_name'] ?? json['user_name'] ?? '',
    );
  }
}

class CardNode extends PresentationNode {
  final String title;
  final String description;
  final List<String> tags;

  CardNode({required super.id, required this.title, required this.description, required this.tags})
      : super(type: 'card');

  factory CardNode.fromJson(Map<String, dynamic> json) {
    return CardNode(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      tags: (json['tags'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
    );
  }
}

class GridNode extends PresentationNode {
  final int columns;
  final List<PresentationNode> items;

  GridNode({required super.id, required this.columns, required this.items}) : super(type: 'grid');

  factory GridNode.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    return GridNode(
      id: json['id'] ?? '',
      columns: json['columns'] ?? 2,
      items: rawItems.map((e) => PresentationNode.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }
}

class SectionNode extends PresentationNode {
  final String title;
  final String content;

  SectionNode({required super.id, required this.title, required this.content})
      : super(type: 'section');

  factory SectionNode.fromJson(Map<String, dynamic> json) {
    return SectionNode(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      content: json['content'] ?? '',
    );
  }
}

class EventCardNode extends PresentationNode {
  final String title;
  final String startTime;
  final String endTime;
  final String? link;
  final String? eventId;

  EventCardNode({
    required super.id,
    required this.title,
    required this.startTime,
    required this.endTime,
    this.link,
    this.eventId,
  }) : super(type: 'EventCard');

  factory EventCardNode.fromJson(Map<String, dynamic> json) {
    return EventCardNode(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      startTime: json['start_time'] ?? json['startTime'] ?? '',
      endTime: json['end_time'] ?? json['endTime'] ?? '',
      link: json['link'] ?? json['url'],
      eventId: json['event_id'] ?? json['eventId'],
    );
  }
}

