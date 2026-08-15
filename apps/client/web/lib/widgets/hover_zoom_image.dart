import 'package:flutter/material.dart';

class HoverZoomImage extends StatefulWidget {
  final Widget child;
  final double scale;
  final Duration duration;
  final BorderRadiusGeometry? borderRadius;

  const HoverZoomImage({
    Key? key,
    required this.child,
    this.scale = 1.05,
    this.duration = const Duration(seconds: 10),
    this.borderRadius,
  }) : super(key: key);

  @override
  State<HoverZoomImage> createState() => _HoverZoomImageState();
}

class _HoverZoomImageState extends State<HoverZoomImage> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    Widget content = AnimatedScale(
      scale: _isHovered ? widget.scale : 1.0,
      duration: widget.duration,
      curve: Curves.easeOut,
      child: widget.child,
    );

    if (widget.borderRadius != null) {
      content = ClipRRect(
        borderRadius: widget.borderRadius!,
        child: content,
      );
    }

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: content,
    );
  }
}
