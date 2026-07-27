abstract class PresentationNode {
  final String id;
  final String type;

  PresentationNode({required this.id, required this.type});

  factory PresentationNode.fromJson(Map<String, dynamic> json) {
    final type = json['type'] as String?;
    final id = json['id'] as String? ?? 'unknown';

    switch (type) {
      case 'Heading':
        return HeadingNode.fromJson(json);
      case 'Paragraph':
        return ParagraphNode.fromJson(json);
      case 'BulletList':
        return BulletListNode.fromJson(json);
      case 'NumberedList':
        return NumberedListNode.fromJson(json);
      case 'NewsCard':
        return NewsCardNode.fromJson(json);
      case 'WeatherCard':
        return WeatherCardNode.fromJson(json);
      case 'ComparisonTable':
        return ComparisonTableNode.fromJson(json);
      case 'CodeBlock':
        return CodeBlockNode.fromJson(json);
      case 'ImageGallery':
        return ImageGalleryNode.fromJson(json);
      case 'Timeline':
        return TimelineNode.fromJson(json);
      case 'Accordion':
        return AccordionNode.fromJson(json);
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

  NewsCardNode({
    required super.id,
    required this.title,
    required this.summary,
    required this.source,
    this.url,
    this.imageUrl,
  }) : super(type: 'NewsCard');

  factory NewsCardNode.fromJson(Map<String, dynamic> json) {
    return NewsCardNode(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      summary: json['summary'] ?? '',
      source: json['source'] ?? '',
      url: json['url'],
      imageUrl: json['imageUrl'],
    );
  }
}

class WeatherCardNode extends PresentationNode {
  final String location;
  final double temperatureC;
  final String condition;
  final List<dynamic> forecast;
  final List<dynamic> hourly;

  WeatherCardNode({
    required super.id,
    required this.location,
    required this.temperatureC,
    required this.condition,
    this.forecast = const [],
    this.hourly = const [],
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
      hourly: json['hourly'] ?? [],
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
  final List<Map<String, String>> images;

  ImageGalleryNode({required super.id, required this.images}) : super(type: 'ImageGallery');

  factory ImageGalleryNode.fromJson(Map<String, dynamic> json) {
    final rawImages = json['images'] as List<dynamic>? ?? [];
    return ImageGalleryNode(
      id: json['id'] ?? '',
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
