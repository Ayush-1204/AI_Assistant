import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class FullScreenGallery extends StatefulWidget {
  final List<Map<String, String>> images;
  final int initialIndex;

  const FullScreenGallery({super.key, required this.images, this.initialIndex = 0});

  @override
  State<FullScreenGallery> createState() => _FullScreenGalleryState();
}

class _FullScreenGalleryState extends State<FullScreenGallery> {
  late PageController _pageController;
  late int _currentIndex;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
    _pageController = PageController(initialPage: widget.initialIndex);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  void _nextPage() {
    if (_currentIndex < widget.images.length - 1) {
      _pageController.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
    }
  }

  void _previousPage() {
    if (_currentIndex > 0) {
      _pageController.previousPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
    }
  }

  String? _proxiedImage(String? url) {
    if (url == null || url.isEmpty) return null;
    
    // Do not proxy local backend URLs!
    if (url.contains('localhost') || url.contains('127.0.0.1')) {
      return url;
    }
    
    // Clean Wikipedia/Wikimedia URLs to avoid wsrv.nl cache corruption or encoding bugs
    String cleanUrl = url;
    if (cleanUrl.contains('?utm_') || cleanUrl.contains('&utm_')) {
      cleanUrl = cleanUrl.split('?').first;
    }
    
    final encoded = Uri.encodeComponent(cleanUrl);
    // Remove w, h, and fit=cover to get original aspect ratio and full size
    return 'https://wsrv.nl/?url=$encoded&output=jpg';
  }

  void _openOriginalUrl(String? url) async {
    if (url == null || url.isEmpty) return;
    try {
      final uri = Uri.parse(url);
      // ignore: deprecated_member_use
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (e) {
      // Ignore
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // The sliding images
          PageView.builder(
            controller: _pageController,
            onPageChanged: (index) {
              setState(() {
                _currentIndex = index;
              });
            },
            itemCount: widget.images.length,
            itemBuilder: (context, index) {
              final img = widget.images[index];
              final url = _proxiedImage(img['url']);
              if (url == null) return const Center(child: Icon(Icons.broken_image, color: Colors.white, size: 48));
              return InteractiveViewer(
                child: Image.network(
                  url,
                  fit: BoxFit.contain,
                  loadingBuilder: (_, child, progress) {
                    if (progress == null) return child;
                    return const Center(child: CircularProgressIndicator(color: Colors.white));
                  },
                  errorBuilder: (_, __, ___) => const Center(child: Icon(Icons.broken_image, color: Colors.white, size: 48)),
                ),
              );
            },
          ),
          
          // Close button
          Positioned(
            top: 40,
            right: 20,
            child: IconButton(
              icon: const Icon(Icons.close, color: Colors.white, size: 32),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
          
          // Image index indicator
          Positioned(
            top: 40,
            left: 20,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.black54,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                '${_currentIndex + 1} / ${widget.images.length}',
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
              ),
            ),
          ),
          
          // Left arrow
          if (_currentIndex > 0)
            Positioned(
              left: 20,
              top: MediaQuery.of(context).size.height / 2 - 24,
              child: IconButton(
                icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 36),
                onPressed: _previousPage,
              ),
            ),
            
          // Right arrow
          if (_currentIndex < widget.images.length - 1)
            Positioned(
              right: 20,
              top: MediaQuery.of(context).size.height / 2 - 24,
              child: IconButton(
                icon: const Icon(Icons.arrow_forward_ios, color: Colors.white, size: 36),
                onPressed: _nextPage,
              ),
            ),
            
          // Bottom metadata bar
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.bottomCenter,
                  end: Alignment.topCenter,
                  colors: [Colors.black87, Colors.transparent],
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      widget.images[_currentIndex]['alt'] ?? '',
                      style: const TextStyle(color: Colors.white, fontSize: 16),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 16),
                  TextButton.icon(
                    icon: const Icon(Icons.download, color: Colors.white, size: 16),
                    label: const Text('Download', style: TextStyle(color: Colors.white)),
                    style: TextButton.styleFrom(
                      backgroundColor: Colors.white24,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    onPressed: () => _openOriginalUrl(widget.images[_currentIndex]['url']),
                  ),
                  const SizedBox(width: 8),
                  TextButton.icon(
                    icon: const Icon(Icons.open_in_new, color: Colors.white, size: 16),
                    label: const Text('Open Original', style: TextStyle(color: Colors.white)),
                    style: TextButton.styleFrom(
                      backgroundColor: Colors.white24,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    onPressed: () => _openOriginalUrl(widget.images[_currentIndex]['url']),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
