import 'package:flutter/material.dart';
import 'models.dart';

class WeatherCardWidget extends StatefulWidget {
  final WeatherCardNode node;
  const WeatherCardWidget({super.key, required this.node});

  @override
  State<WeatherCardWidget> createState() => _WeatherCardWidgetState();
}

class _WeatherCardWidgetState extends State<WeatherCardWidget> {
  int _selectedDayIndex = 0;
  bool _isFahrenheit = false;
  String _selectedMetric = 'Temperature';

  String _getEmojiForCondition(String condition) {
    final lower = condition.toLowerCase();
    if (lower.contains('storm')) return '⛈️';
    if (lower.contains('rain') || lower.contains('drizzle')) return '🌧️';
    if (lower.contains('snow')) return '❄️';
    if (lower.contains('cloud') || lower.contains('overcast')) return '☁️';
    if (lower.contains('fog')) return '🌫️';
    if (lower.contains('clear')) return '☀️';
    return '⛅';
  }

  @override
  Widget build(BuildContext context) {
    final node = widget.node;
    final hasForecast = node.forecast.isNotEmpty;
    
    // Determine which day's data to show
    final selectedForecast = hasForecast && _selectedDayIndex < node.forecast.length 
        ? node.forecast[_selectedDayIndex] 
        : null;
        
    final displayTemp = _selectedDayIndex == 0 
        ? node.temperatureC 
        : (selectedForecast != null ? (selectedForecast['high'] as num?)?.toDouble() ?? 0.0 : 0.0);
        
    final displayTempConverted = _isFahrenheit ? (displayTemp * 9 / 5) + 32 : displayTemp;

    final displayCondition = _selectedDayIndex == 0
        ? node.condition
        : (selectedForecast != null ? selectedForecast['condition'] as String? ?? 'Unknown' : 'Unknown');

    final hourlyData = selectedForecast != null && selectedForecast['hourly'] != null
        ? selectedForecast['hourly'] as List<dynamic>
        : <dynamic>[];

    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 500),
      child: Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      padding: const EdgeInsets.all(16),
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
                '${displayTempConverted.round()}°',
                style: const TextStyle(fontSize: 48, fontWeight: FontWeight.w400, color: Colors.white, height: 1),
              ),
              Padding(
                padding: const EdgeInsets.only(top: 4.0, left: 8.0),
                child: Row(
                  children: [
                    GestureDetector(
                      onTap: () => setState(() => _isFahrenheit = false),
                      child: Text('C', style: TextStyle(fontSize: 16, color: !_isFahrenheit ? Colors.white : Colors.white54, fontWeight: FontWeight.w500)),
                    ),
                    const Text(' / ', style: TextStyle(fontSize: 16, color: Colors.white54)),
                    GestureDetector(
                      onTap: () => setState(() => _isFahrenheit = true),
                      child: Text('F', style: TextStyle(fontSize: 16, color: _isFahrenheit ? Colors.white : Colors.white54, fontWeight: FontWeight.w500)),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            displayCondition,
            style: const TextStyle(fontSize: 18, color: Colors.white),
          ),
          const SizedBox(height: 16),
          
          if (hasForecast)
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: List.generate(node.forecast.length, (index) {
                final f = node.forecast[index];
                final isSelected = index == _selectedDayIndex;
                return Expanded(
                  child: GestureDetector(
                    onTap: () {
                      setState(() {
                        _selectedDayIndex = index;
                      });
                    },
                    child: Container(
                      margin: const EdgeInsets.only(right: 4),
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      decoration: BoxDecoration(
                        color: isSelected ? Colors.white.withValues(alpha: 0.1) : Colors.transparent,
                        borderRadius: BorderRadius.circular(12),
                        border: isSelected 
                            ? Border.all(color: Colors.blue.withValues(alpha: 0.5)) 
                            : Border.all(color: Colors.transparent),
                      ),
                      child: Column(
                        children: [
                          Text(f['day'] ?? '', style: TextStyle(color: isSelected ? Colors.white : Colors.white70, fontWeight: FontWeight.w600, fontSize: 13)),
                          const SizedBox(height: 4),
                          Text(_getEmojiForCondition(f['condition'] ?? ''), style: const TextStyle(fontSize: 24)),
                          const SizedBox(height: 4),
                          Text('${(_isFahrenheit ? (((f['high'] as num?) ?? 0) * 9/5) + 32 : ((f['high'] as num?) ?? 0)).round()}°', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14)),
                          const SizedBox(height: 2),
                          Text('${(_isFahrenheit ? (((f['low'] as num?) ?? 0) * 9/5) + 32 : ((f['low'] as num?) ?? 0)).round()}°', style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 12)),
                        ],
                      ),
                    ),
                  ),
                );
              }),
            ),
            
          if (hourlyData.isNotEmpty) ...[
            const SizedBox(height: 16),
          DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: _selectedMetric,
              dropdownColor: const Color(0xFF303134),
              icon: Icon(Icons.unfold_more, color: Colors.white.withValues(alpha: 0.5), size: 16),
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
              onChanged: (String? newValue) {
                if (newValue != null) setState(() => _selectedMetric = newValue);
              },
              items: <String>['Temperature', 'Precipitation']
                  .map<DropdownMenuItem<String>>((String value) {
                return DropdownMenuItem<String>(
                  value: value,
                  child: Text(value),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 12),
          
          SizedBox(
            height: 80,
            width: double.infinity,
            child: CustomPaint(
              painter: _HourlyDataPainter(hourly: hourlyData, isFahrenheit: _isFahrenheit, metric: _selectedMetric),
            ),
          )
          ]
        ],
      ),
      ),
    );
  }
}

class _HourlyDataPainter extends CustomPainter {
  final List<dynamic> hourly;
  final bool isFahrenheit;
  final String metric;

  _HourlyDataPainter({required this.hourly, required this.isFahrenheit, required this.metric});

  @override
  void paint(Canvas canvas, Size size) {
    if (hourly.isEmpty) return;

    final double width = size.width;
    final double height = size.height;
    
    double minVal = double.infinity;
    double maxVal = double.negativeInfinity;
    for (var h in hourly) {
      double v = metric == 'Temperature' 
          ? (isFahrenheit ? (((h['temp'] as num).toDouble() * 9/5) + 32) : (h['temp'] as num).toDouble())
          : (h['precip'] as num?)?.toDouble() ?? 0.0;
      if (v < minVal) minVal = v;
      if (v > maxVal) maxVal = v;
    }
    
    if (metric == 'Temperature') {
      minVal -= 2;
      maxVal += 2;
    } else {
      minVal = 0;
      maxVal = maxVal < 20 ? 20 : (maxVal > 100 ? 100 : maxVal * 1.5);
    }
    double range = maxVal - minVal;
    if (range == 0) range = 1;

    if (metric == 'Precipitation') {
      // Draw Bar Chart
      final Paint barPaint = Paint()
        ..color = const Color(0xFF356AC2)
        ..style = PaintingStyle.fill;
        
      final double barWidth = width / hourly.length;
      
      for (int i = 0; i < hourly.length; i++) {
        double v = (hourly[i]['precip'] as num?)?.toDouble() ?? 0.0;
        double barHeight = (v / maxVal) * (height - 40);
        if (barHeight < 2) barHeight = 2; // small baseline
        
        Rect barRect = Rect.fromLTWH(i * barWidth, height - 20 - barHeight, barWidth, barHeight);
        canvas.drawRect(barRect, barPaint);
        
        final valStr = '${v.round()}%';
        final textPainter = TextPainter(
          text: TextSpan(text: valStr, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
          textDirection: TextDirection.ltr,
        );
        textPainter.layout();
        textPainter.paint(canvas, Offset(i * barWidth + (barWidth - textPainter.width) / 2, height - 20 - barHeight - 18));
        
        final timeStr = hourly[i]['time'] ?? '';
        final timePainter = TextPainter(
          text: TextSpan(text: timeStr, style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 12)),
          textDirection: TextDirection.ltr,
        );
        timePainter.layout();
        timePainter.paint(canvas, Offset(i * barWidth + (barWidth - timePainter.width) / 2, height - 15));
      }
    } else {
      // Draw Line Chart for Temperature
      final double stepX = width / (hourly.length > 1 ? hourly.length - 1 : 1);
      
      List<Offset> points = [];
      for (int i = 0; i < hourly.length; i++) {
        double v = (isFahrenheit ? (((hourly[i]['temp'] as num).toDouble() * 9/5) + 32) : (hourly[i]['temp'] as num).toDouble());
        double x = i * stepX;
        double y = height - ((v - minVal) / range) * (height - 40); 
        points.add(Offset(x, y - 20)); 
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
        
        double v = (isFahrenheit ? (((hourly[i]['temp'] as num).toDouble() * 9/5) + 32) : (hourly[i]['temp'] as num).toDouble());
        
        final valStr = '${v.round()}°';
        final textPainter = TextPainter(
          text: TextSpan(text: valStr, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
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
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
