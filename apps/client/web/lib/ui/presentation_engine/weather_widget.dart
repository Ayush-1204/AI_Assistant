import 'package:flutter/material.dart';
import 'models.dart';

class WeatherCardWidget extends StatelessWidget {
  final WeatherCardNode node;
  const WeatherCardWidget({super.key, required this.node});

  IconData _getIconForCondition(String condition) {
    final lower = condition.toLowerCase();
    if (lower.contains('rain')) return Icons.water_drop;
    if (lower.contains('snow')) return Icons.ac_unit;
    if (lower.contains('cloud')) return Icons.cloud;
    if (lower.contains('storm')) return Icons.thunderstorm;
    if (lower.contains('fog')) return Icons.foggy;
    return Icons.wb_sunny;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 16),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF202124),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            node.location,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Colors.white),
          ),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${node.temperatureC.round()}°',
                style: const TextStyle(fontSize: 64, fontWeight: FontWeight.w400, color: Colors.white, height: 1),
              ),
              const Padding(
                padding: EdgeInsets.only(top: 8.0, left: 8.0),
                child: Text(
                  'C / F',
                  style: TextStyle(fontSize: 16, color: Colors.white70, fontWeight: FontWeight.w500),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            node.condition,
            style: const TextStyle(fontSize: 18, color: Colors.white),
          ),
          const SizedBox(height: 32),
          
          if (node.forecast.isNotEmpty)
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: node.forecast.map((f) {
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Column(
                      children: [
                        Text(f['day'] ?? '', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                        const SizedBox(height: 8),
                        Icon(_getIconForCondition(f['condition'] ?? ''), color: Colors.white, size: 24),
                        const SizedBox(height: 8),
                        Text('${(f['high'] as num?)?.round() ?? 0}°', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                        const SizedBox(height: 4),
                        Text('${(f['low'] as num?)?.round() ?? 0}°', style: TextStyle(color: Colors.white.withValues(alpha: 0.5))),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ),
            
          const SizedBox(height: 32),
          Row(
            children: [
              const Text('Temperature', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
              const SizedBox(width: 4),
              Icon(Icons.unfold_more, color: Colors.white.withValues(alpha: 0.5), size: 16),
            ],
          ),
          const SizedBox(height: 24),
          
          if (node.hourly.isNotEmpty)
            SizedBox(
              height: 120,
              width: double.infinity,
              child: CustomPaint(
                painter: _HourlyTemperaturePainter(hourly: node.hourly),
              ),
            ),
            
          const SizedBox(height: 16),
          Align(
            alignment: Alignment.bottomRight,
            child: Text(
              'Give feedback',
              style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 12),
            ),
          )
        ],
      ),
    );
  }
}

class _HourlyTemperaturePainter extends CustomPainter {
  final List<dynamic> hourly;

  _HourlyTemperaturePainter({required this.hourly});

  @override
  void paint(Canvas canvas, Size size) {
    if (hourly.isEmpty) return;

    final double width = size.width;
    final double height = size.height;
    
    double minTemp = double.infinity;
    double maxTemp = double.negativeInfinity;
    for (var h in hourly) {
      double t = (h['temp'] as num).toDouble();
      if (t < minTemp) minTemp = t;
      if (t > maxTemp) maxTemp = t;
    }
    
    minTemp -= 2;
    maxTemp += 2;
    double range = maxTemp - minTemp;
    if (range == 0) range = 1;

    final double stepX = width / (hourly.length > 1 ? hourly.length - 1 : 1);
    
    List<Offset> points = [];
    for (int i = 0; i < hourly.length; i++) {
      double t = (hourly[i]['temp'] as num).toDouble();
      double x = i * stepX;
      double y = height - ((t - minTemp) / range) * (height - 40); 
      points.add(Offset(x, y - 20)); // Adjust y upwards for labels
    }

    Path path = Path();
    path.moveTo(points.first.dx, points.first.dy);
    
    for (int i = 0; i < points.length - 1; i++) {
      final p0 = points[i];
      final p1 = points[i + 1];
      
      final cx = (p0.dx + p1.dx) / 2;
      path.cubicTo(cx, p0.dy, cx, p1.dy, p1.dx, p1.dy);
    }

    final linePaint = Paint()
      ..color = Colors.white
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;
    canvas.drawPath(path, linePaint);

    Path fillPath = Path.from(path);
    fillPath.lineTo(points.last.dx, height - 20);
    fillPath.lineTo(points.first.dx, height - 20);
    fillPath.close();

    final fillPaint = Paint()
      ..shader = LinearGradient(
        colors: [
          Colors.orange.withValues(alpha: 0.3),
          Colors.orange.withValues(alpha: 0.0),
        ],
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
      ).createShader(Rect.fromLTWH(0, 0, width, height));
      
    canvas.drawPath(fillPath, fillPaint);

    final dotPaint = Paint()..color = Colors.white;
    final dotBgPaint = Paint()..color = const Color(0xFF202124);
    
    for (int i = 0; i < points.length; i++) {
      final p = points[i];
      
      canvas.drawCircle(p, 4, dotBgPaint);
      canvas.drawCircle(p, 3, dotPaint);
      
      final tempStr = '${(hourly[i]['temp'] as num).round()}°';
      final textPainter = TextPainter(
        text: TextSpan(text: tempStr, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
        textDirection: TextDirection.ltr,
      );
      textPainter.layout();
      textPainter.paint(canvas, Offset(p.dx - textPainter.width / 2, p.dy - 20));
      
      final timeStr = hourly[i]['time'] ?? '';
      final timePainter = TextPainter(
        text: TextSpan(text: timeStr, style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 12)),
        textDirection: TextDirection.ltr,
      );
      timePainter.layout();
      timePainter.paint(canvas, Offset(p.dx - timePainter.width / 2, height - 15));
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
