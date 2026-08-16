import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:file_picker/file_picker.dart';
import 'package:syncfusion_flutter_pdfviewer/pdfviewer.dart';
import 'providers/library_provider.dart';
import 'providers/auth_provider.dart';
import 'api_client.dart';
import 'widgets/hover_zoom_image.dart';
import 'package:url_launcher/url_launcher.dart';

class LibraryView extends ConsumerStatefulWidget {
  const LibraryView({super.key});

  @override
  ConsumerState<LibraryView> createState() => _LibraryViewState();
}

class _LibraryViewState extends ConsumerState<LibraryView> {
  String _searchQuery = '';
  bool _isGridView = false;
  
  Set<String> _selectedSources = {'Uploaded'};
  Set<String> _selectedFileTypes = {'Show all file types'};
  Set<int> _selectedIds = {};
  bool _showDeleted = false;

  void _uploadFile() async {
    FilePickerResult? result = await FilePicker.pickFiles(
      withData: true,
      allowMultiple: true,
    );

    if (result != null) {
      final apiClient = ref.read(apiClientProvider);
      for (var file in result.files) {
        if (file.bytes != null) {
          try {
            await apiClient.uploadDocument(file.name, file.bytes!, file.name);
          } catch (e) {
            debugPrint("Upload failed: $e");
          }
        }
      }
      ref.invalidate(libraryProvider);
    }
  }

  void _openFile(Map<String, dynamic> doc) async {
    final documentId = doc['id'];
    final token = ref.read(authProvider).token;
    final url = '${ApiClient.baseUrl}/documents/$documentId/download?token=$token';
    
    final mime = (doc['mime_type'] ?? '').toString().toLowerCase();
    final ext = (doc['original_filename'] ?? '').toString().split('.').last.toLowerCase();
    final isImg = mime.startsWith('image/') || ['png', 'jpg', 'jpeg', 'gif', 'webp'].contains(ext);
    final isPdf = mime == 'application/pdf' || ext == 'pdf';

    if (isImg) {
      if (context.mounted) {
        showDialog(
          context: context,
          builder: (context) => Dialog(
            backgroundColor: Colors.transparent,
            insetPadding: const EdgeInsets.all(24),
            child: Stack(
              alignment: Alignment.topRight,
              children: [
                InteractiveViewer(
                  child: Image.network(url),
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: const Icon(Icons.download, color: Colors.white),
                      onPressed: () async {
                        final uri = Uri.parse(url);
                        if (await canLaunchUrl(uri)) {
                          await launchUrl(uri, webOnlyWindowName: '_blank');
                        }
                      },
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, color: Colors.white),
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      }
      return;
    }



    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, webOnlyWindowName: '_blank');
    }
  }

  void _deleteDocument(int documentId) async {
    try {
      await ref.read(apiClientProvider).deleteDocument(documentId, hard: _showDeleted);
      ref.invalidate(libraryProvider);
    } catch (e) {
      debugPrint("Delete failed: \$e");
    }
  }

  void _bulkDeleteDocuments() async {
    try {
      await ref.read(apiClientProvider).bulkDeleteDocuments(_selectedIds.toList(), hard: _showDeleted);
      setState(() {
        _selectedIds.clear();
      });
      ref.invalidate(libraryProvider);
    } catch (e) {
      debugPrint("Bulk delete failed: \$e");
    }
  }

  @override
  Widget build(BuildContext context) {
    final docsAsync = ref.watch(libraryProvider(_showDeleted));

    return Scaffold(
      backgroundColor: Colors.black,
      body: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // SIDEBAR
          Container(
            width: 260,
            padding: const EdgeInsets.all(32.0),
            decoration: BoxDecoration(
              border: Border(right: BorderSide(color: Colors.white.withValues(alpha: 0.05))),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Library',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 40),
                
                // SOURCE SECTION
                Text('Source', style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 13, fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                _buildSidebarItem('Uploaded', Icons.upload_outlined, _selectedSources.contains('Uploaded') && !_showDeleted, () {
                  setState(() {
                    _showDeleted = false;
                    if (_selectedSources.contains('Uploaded')) _selectedSources.remove('Uploaded');
                    else _selectedSources.add('Uploaded');
                  });
                }),
                _buildSidebarItem('Generated', Icons.auto_awesome_outlined, _selectedSources.contains('Generated') && !_showDeleted, () {
                  setState(() {
                    _showDeleted = false;
                    if (_selectedSources.contains('Generated')) _selectedSources.remove('Generated');
                    else _selectedSources.add('Generated');
                  });
                }),
                
                const SizedBox(height: 32),
                
                // FILE TYPE SECTION
                Text('File type', style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 13, fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),
                _buildSidebarItem('Images', Icons.image_outlined, _selectedFileTypes.contains('Images'), () => _toggleFileType('Images')),
                _buildSidebarItem('Documents', Icons.article_outlined, _selectedFileTypes.contains('Documents'), () => _toggleFileType('Documents')),
                _buildSidebarItem('Spreadsheets', Icons.grid_on_outlined, _selectedFileTypes.contains('Spreadsheets'), () => _toggleFileType('Spreadsheets')),
                _buildSidebarItem('Presentations', Icons.slideshow_outlined, _selectedFileTypes.contains('Presentations'), () => _toggleFileType('Presentations')),
                _buildSidebarItem('PDFs', Icons.picture_as_pdf_outlined, _selectedFileTypes.contains('PDFs'), () => _toggleFileType('PDFs')),
                const SizedBox(height: 8),
                _buildSidebarItem('Show all file types', Icons.visibility_outlined, _selectedFileTypes.contains('Show all file types'), () {
                  setState(() {
                    _selectedFileTypes.clear();
                    _selectedFileTypes.add('Show all file types');
                  });
                }),
                
                const Spacer(),
                _buildSidebarItem('Recently deleted', Icons.delete_outline, _showDeleted, () {
                  setState(() {
                    _showDeleted = true;
                  });
                }, color: _showDeleted ? Colors.white : Colors.white.withValues(alpha: 0.5)),
              ],
            ),
          ),
          
          // MAIN CONTENT
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(32.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Top Bar (Search + Upload) or Selection Action Bar
                  _selectedIds.isNotEmpty
                      ? Row(
                          children: [
                            ElevatedButton.icon(
                              onPressed: () {},
                              icon: const Icon(Icons.chat_bubble_outline, size: 18),
                              label: const Text('Start chat', style: TextStyle(fontWeight: FontWeight.bold)),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.white,
                                foregroundColor: Colors.black,
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                              ),
                            ),
                            const SizedBox(width: 12),
                            OutlinedButton.icon(
                              onPressed: () {},
                              icon: const Icon(Icons.download, size: 18),
                              label: const Text('Download', style: TextStyle(fontWeight: FontWeight.bold)),
                              style: OutlinedButton.styleFrom(
                                foregroundColor: Colors.white,
                                side: BorderSide(color: Colors.white.withValues(alpha: 0.2)),
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                              ),
                            ),
                            const SizedBox(width: 12),
                            OutlinedButton.icon(
                              onPressed: () {},
                              icon: const Icon(Icons.drive_file_move_outline, size: 18),
                              label: const Text('Move', style: TextStyle(fontWeight: FontWeight.bold)),
                              style: OutlinedButton.styleFrom(
                                foregroundColor: Colors.white,
                                side: BorderSide(color: Colors.white.withValues(alpha: 0.2)),
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                              ),
                            ),
                            const SizedBox(width: 12),
                            OutlinedButton.icon(
                              onPressed: _bulkDeleteDocuments,
                              icon: const Icon(Icons.delete_outline, size: 18),
                              label: const Text('Delete', style: TextStyle(fontWeight: FontWeight.bold)),
                              style: OutlinedButton.styleFrom(
                                foregroundColor: Colors.redAccent,
                                side: BorderSide(color: Colors.redAccent.withValues(alpha: 0.5)),
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                              ),
                            ),
                            const Spacer(),
                            Text('${_selectedIds.length} selected', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                            const SizedBox(width: 24),
                            IconButton(
                              icon: Icon(Icons.grid_view, color: _isGridView ? Colors.white : Colors.white.withValues(alpha: 0.5)),
                              onPressed: () => setState(() => _isGridView = true),
                            ),
                            IconButton(
                              icon: Icon(Icons.list, color: !_isGridView ? Colors.white : Colors.white.withValues(alpha: 0.5)),
                              onPressed: () => setState(() => _isGridView = false),
                            ),
                          ],
                        )
                      : Row(
                          children: [
                            Container(
                              width: 300,
                              height: 40,
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: TextField(
                                style: const TextStyle(color: Colors.white, fontSize: 14),
                                decoration: InputDecoration(
                                  hintText: 'Search',
                                  hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.5)),
                                  prefixIcon: Icon(Icons.search, color: Colors.white.withValues(alpha: 0.5), size: 20),
                                  border: InputBorder.none,
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                                ),
                                onChanged: (val) {
                                  setState(() {
                                    _searchQuery = val;
                                  });
                                },
                              ),
                            ),
                            const Spacer(),
                            IconButton(
                              icon: Icon(Icons.grid_view, color: _isGridView ? Colors.white : Colors.white.withValues(alpha: 0.5)),
                              onPressed: () => setState(() => _isGridView = true),
                            ),
                            IconButton(
                              icon: Icon(Icons.list, color: !_isGridView ? Colors.white : Colors.white.withValues(alpha: 0.5)),
                              onPressed: () => setState(() => _isGridView = false),
                            ),
                            const SizedBox(width: 16),
                            ElevatedButton(
                              onPressed: _uploadFile,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.white,
                                foregroundColor: Colors.black,
                                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(24),
                                ),
                              ),
                              child: const Text('Upload file', style: TextStyle(fontWeight: FontWeight.bold)),
                            ),
                          ],
                        ),
                  const SizedBox(height: 32),
                  
                  // Document Grid/List
                  Expanded(
                    child: docsAsync.when(
                      data: (docs) {
                        var filtered = docs.where((doc) {
                          final title = (doc['title'] ?? '').toString().toLowerCase();
                          final mime = (doc['mime_type'] ?? '').toString().toLowerCase();
                          final ext = (doc['original_filename'] ?? '').toString().toLowerCase().split('.').last;
                          
                          if (_searchQuery.isNotEmpty && !title.contains(_searchQuery.toLowerCase())) {
                            return false;
                          }

                          // Source filter (all our files are uploaded for now)
                          if (!_selectedSources.contains('Uploaded') && _selectedSources.isNotEmpty) {
                            return false;
                          }

                          // Type filter
                          if (!_selectedFileTypes.contains('Show all file types') && _selectedFileTypes.isNotEmpty) {
                            bool isImg = mime.startsWith('image/') || ['png', 'jpg', 'jpeg', 'gif', 'webp'].contains(ext);
                            bool isDoc = mime.contains('word') || mime.contains('text') || ext == 'doc' || ext == 'docx' || ext == 'txt';
                            bool isSheet = mime.contains('excel') || mime.contains('spreadsheet') || ext == 'xls' || ext == 'xlsx' || ext == 'csv';
                            bool isPres = mime.contains('presentation') || ext == 'ppt' || ext == 'pptx';
                            bool isPdf = mime.contains('pdf') || ext == 'pdf';

                            bool matches = false;
                            if (_selectedFileTypes.contains('Images') && isImg) matches = true;
                            if (_selectedFileTypes.contains('Documents') && isDoc) matches = true;
                            if (_selectedFileTypes.contains('Spreadsheets') && isSheet) matches = true;
                            if (_selectedFileTypes.contains('Presentations') && isPres) matches = true;
                            if (_selectedFileTypes.contains('PDFs') && isPdf) matches = true;

                            if (!matches) return false;
                          }

                          return true;
                        }).toList();

                        if (filtered.isEmpty) {
                          return Center(
                            child: Text('No files found.', style: TextStyle(color: Colors.white.withValues(alpha: 0.5))),
                          );
                        }

                        if (_isGridView) {
                          return GridView.builder(
                            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                              crossAxisCount: 6,
                              crossAxisSpacing: 16,
                              mainAxisSpacing: 16,
                              childAspectRatio: 1.0,
                            ),
                            itemCount: filtered.length,
                            itemBuilder: (context, index) {
                              return _buildGridCard(filtered[index]);
                            },
                          );
                        } else {
                          return ListView.separated(
                            itemCount: filtered.length + 1,
                            separatorBuilder: (context, index) => Divider(color: Colors.white.withValues(alpha: 0.1)),
                            itemBuilder: (context, index) {
                              if (index == 0) {
                                return Padding(
                                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                  child: Row(
                                    children: [
                                      Expanded(flex: 3, child: Text('Name', style: TextStyle(color: Colors.white.withValues(alpha: 0.5)))),
                                      Expanded(flex: 1, child: Text('Modified', style: TextStyle(color: Colors.white.withValues(alpha: 0.5)))),
                                      Expanded(flex: 1, child: Text('Size', style: TextStyle(color: Colors.white.withValues(alpha: 0.5)))),
                                    ],
                                  ),
                                );
                              }
                              return _buildListItem(filtered[index - 1]);
                            },
                          );
                        }
                      },
                      loading: () => const Center(child: CircularProgressIndicator(color: Colors.white)),
                      error: (err, stack) => Center(child: Text('Error: $err', style: const TextStyle(color: Colors.red))),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  void _toggleFileType(String type) {
    setState(() {
      _selectedFileTypes.remove('Show all file types');
      if (_selectedFileTypes.contains(type)) {
        _selectedFileTypes.remove(type);
      } else {
        _selectedFileTypes.add(type);
      }
      if (_selectedFileTypes.isEmpty) {
        _selectedFileTypes.add('Show all file types');
      }
    });
  }

  Widget _buildSidebarItem(String label, IconData icon, bool isActive, VoidCallback onTap, {Color? color}) {
    final itemColor = color ?? (isActive ? Colors.white : Colors.white.withValues(alpha: 0.7));
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          color: isActive ? Colors.white.withValues(alpha: 0.1) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Icon(icon, size: 20, color: itemColor),
            const SizedBox(width: 12),
            Text(label, style: TextStyle(color: itemColor, fontSize: 14, fontWeight: isActive ? FontWeight.w600 : FontWeight.normal)),
          ],
        ),
      ),
    );
  }

  String _formatSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(2)} MB';
  }

  String _formatDate(String isoString) {
    try {
      final date = DateTime.parse(isoString).toLocal();
      return DateFormat('MMM d').format(date);
    } catch (_) {
      return '';
    }
  }

  Widget _buildFileIcon(String ext, {double size = 24}) {
    Color extColor = Colors.grey;
    if (ext == 'pdf') extColor = Colors.redAccent;
    else if (ext == 'doc' || ext == 'docx') extColor = Colors.blueAccent;
    else if (ext == 'xls' || ext == 'xlsx') extColor = Colors.green;
    else if (ext == 'ppt' || ext == 'pptx') extColor = Colors.orangeAccent;
    else if (ext == 'md') extColor = Colors.orange;
    else if (['png', 'jpg', 'jpeg', 'gif', 'webp'].contains(ext)) extColor = Colors.purpleAccent;

    return Container(
      width: size * 1.5,
      height: size * 1.5,
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(8),
      ),
      alignment: Alignment.center,
      child: Icon(
        ['png', 'jpg', 'jpeg', 'gif', 'webp'].contains(ext) ? Icons.image_outlined : Icons.insert_drive_file_outlined,
        color: extColor,
        size: size,
      ),
    );
  }

  Widget _buildListItem(Map<String, dynamic> doc) {
    final mime = (doc['mime_type'] ?? '').toString().toLowerCase();
    final ext = (doc['original_filename'] ?? '').toString().split('.').last.toLowerCase();
    bool isImg = mime.startsWith('image/') || ['png', 'jpg', 'jpeg', 'gif', 'webp'].contains(ext);
    final token = ref.read(authProvider).token;
    final imgUrl = '${ApiClient.baseUrl}/documents/${doc['id']}/download?token=$token';
    final int docId = doc['id'];
    
    bool isHovered = false;

    return StatefulBuilder(
      builder: (context, setLocalState) {
        final isSelected = _selectedIds.contains(docId);
        final showOverlay = isHovered || isSelected || _selectedIds.isNotEmpty;

        return InkWell(
          onTap: () {
            if (_selectedIds.isNotEmpty) {
              setState(() {
                if (isSelected) _selectedIds.remove(docId);
                else _selectedIds.add(docId);
              });
            } else {
              _openFile(doc);
            }
          },
          onHover: (hovering) => setLocalState(() => isHovered = hovering),
          hoverColor: Colors.white.withValues(alpha: 0.05),
          child: Container(
            color: isSelected ? Colors.blueAccent.withValues(alpha: 0.1) : Colors.transparent,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                Expanded(
                  flex: 3,
                  child: Row(
                    children: [
                      isImg 
                          ? ClipRRect(
                              borderRadius: BorderRadius.circular(8),
                              child: Image.network(
                                imgUrl, 
                                width: 36, 
                                height: 36, 
                                fit: BoxFit.cover,
                                errorBuilder: (context, error, stackTrace) => _buildFileIcon(ext),
                              ),
                            )
                          : _buildFileIcon(ext),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Text(
                          doc['title'] ?? doc['original_filename'] ?? '',
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  flex: 1,
                  child: Text(
                    _formatDate(doc['created_at'] ?? ''),
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.6)),
                  ),
                ),
                Expanded(
                  flex: 1,
                  child: Text(
                    _formatSize(doc['file_size'] ?? 0),
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.6)),
                  ),
                ),
                if (showOverlay)
                  Row(
                    children: [
                      PopupMenuButton<String>(
                        icon: const Icon(Icons.more_horiz, color: Colors.white, size: 20),
                        color: const Color(0xFF2C2C2C),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        onSelected: (value) {
                          if (value == 'delete') {
                            _deleteDocument(docId);
                          }
                        },
                        itemBuilder: (BuildContext context) => <PopupMenuEntry<String>>[
                          const PopupMenuItem<String>(
                            value: 'chat',
                            child: Row(children: [Icon(Icons.chat_bubble_outline, size: 20, color: Colors.white), SizedBox(width: 12), Text('Chat about this', style: TextStyle(color: Colors.white))]),
                          ),
                          const PopupMenuItem<String>(
                            value: 'download',
                            child: Row(children: [Icon(Icons.download, size: 20, color: Colors.white), SizedBox(width: 12), Text('Download', style: TextStyle(color: Colors.white))]),
                          ),
                          const PopupMenuItem<String>(
                            value: 'rename',
                            child: Row(children: [Icon(Icons.edit_outlined, size: 20, color: Colors.white), SizedBox(width: 12), Text('Rename', style: TextStyle(color: Colors.white))]),
                          ),
                          const PopupMenuItem<String>(
                            value: 'move',
                            child: Row(children: [Icon(Icons.drive_file_move_outline, size: 20, color: Colors.white), SizedBox(width: 12), Text('Move', style: TextStyle(color: Colors.white))]),
                          ),
                          const PopupMenuItem<String>(
                            value: 'delete',
                            child: Row(children: [Icon(Icons.delete_outline, size: 20, color: Colors.redAccent), SizedBox(width: 12), Text('Delete', style: TextStyle(color: Colors.redAccent))]),
                          ),
                        ],
                      ),
                      const SizedBox(width: 8),
                      GestureDetector(
                        onTap: () {
                          setState(() {
                            if (isSelected) _selectedIds.remove(docId);
                            else _selectedIds.add(docId);
                          });
                        },
                        child: Container(
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: isSelected ? Colors.blueAccent : Colors.transparent,
                            border: Border.all(color: isSelected ? Colors.blueAccent : Colors.white.withValues(alpha: 0.5), width: 2),
                          ),
                          padding: const EdgeInsets.all(2),
                          child: Icon(
                            Icons.check,
                            size: 16,
                            color: isSelected ? Colors.white : Colors.transparent,
                          ),
                        ),
                      ),
                    ],
                  )
                else
                  const SizedBox(width: 76), // placeholder to prevent layout shifting
              ],
            ),
          ),
        );
      }
    );
  }

  Widget _buildGridCard(Map<String, dynamic> doc) {
    final mime = (doc['mime_type'] ?? '').toString().toLowerCase();
    final ext = (doc['original_filename'] ?? '').toString().split('.').last.toLowerCase();
    bool isImg = mime.startsWith('image/') || ['png', 'jpg', 'jpeg', 'gif', 'webp'].contains(ext);
    final token = ref.read(authProvider).token;
    final imgUrl = '${ApiClient.baseUrl}/documents/${doc['id']}/download?token=$token';
    final int docId = doc['id'];
    
    bool isHovered = false;
    
    return StatefulBuilder(
      builder: (context, setLocalState) {
        final isSelected = _selectedIds.contains(docId);
        final showOverlay = isHovered || isSelected || _selectedIds.isNotEmpty;

        return InkWell(
          onTap: () {
            if (_selectedIds.isNotEmpty) {
              setState(() {
                if (isSelected) _selectedIds.remove(docId);
                else _selectedIds.add(docId);
              });
            } else {
              _openFile(doc);
            }
          },
          onHover: (hovering) => setLocalState(() => isHovered = hovering),
          child: Container(
            decoration: BoxDecoration(
              color: const Color(0xFF1F1F1F),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: isSelected ? Colors.blueAccent : Colors.white.withValues(alpha: 0.05),
                width: isSelected ? 2 : 1,
              ),
            ),
            clipBehavior: Clip.hardEdge,
            child: Stack(
              children: [
                HoverZoomImage(
                  scale: 1.02,
                  duration: const Duration(milliseconds: 200),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Expanded(
                        child: Center(
                          child: isImg 
                              ? ClipRRect(
                                  borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
                                  child: Image.network(
                                    imgUrl, 
                                    fit: BoxFit.cover, 
                                    width: double.infinity,
                                    height: double.infinity,
                                    errorBuilder: (context, error, stackTrace) => _buildFileIcon(ext, size: 48),
                                  ),
                                )
                              : _buildFileIcon(ext, size: 48),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              doc['title'] ?? doc['original_filename'] ?? '',
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 4),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  _formatDate(doc['created_at'] ?? ''),
                                  style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 12),
                                ),
                                Text(
                                  _formatSize(doc['file_size'] ?? 0),
                                  style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 12),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                if (showOverlay)
                  Positioned(
                    top: 8,
                    right: 8,
                    child: PopupMenuButton<String>(
                      icon: Container(
                        decoration: BoxDecoration(
                          color: Colors.black.withValues(alpha: 0.5),
                          shape: BoxShape.circle,
                        ),
                        padding: const EdgeInsets.all(4),
                        child: const Icon(Icons.more_horiz, color: Colors.white, size: 20),
                      ),
                      color: const Color(0xFF2C2C2C),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      onSelected: (value) {
                        if (value == 'delete') {
                          _deleteDocument(docId);
                        }
                      },
                      itemBuilder: (BuildContext context) => <PopupMenuEntry<String>>[
                        const PopupMenuItem<String>(
                          value: 'chat',
                          child: Row(children: [Icon(Icons.chat_bubble_outline, size: 20, color: Colors.white), SizedBox(width: 12), Text('Chat about this', style: TextStyle(color: Colors.white))]),
                        ),
                        const PopupMenuItem<String>(
                          value: 'download',
                          child: Row(children: [Icon(Icons.download, size: 20, color: Colors.white), SizedBox(width: 12), Text('Download', style: TextStyle(color: Colors.white))]),
                        ),
                        const PopupMenuItem<String>(
                          value: 'rename',
                          child: Row(children: [Icon(Icons.edit_outlined, size: 20, color: Colors.white), SizedBox(width: 12), Text('Rename', style: TextStyle(color: Colors.white))]),
                        ),
                        const PopupMenuItem<String>(
                          value: 'move',
                          child: Row(children: [Icon(Icons.drive_file_move_outline, size: 20, color: Colors.white), SizedBox(width: 12), Text('Move', style: TextStyle(color: Colors.white))]),
                        ),
                        const PopupMenuItem<String>(
                          value: 'delete',
                          child: Row(children: [Icon(Icons.delete_outline, size: 20, color: Colors.redAccent), SizedBox(width: 12), Text('Delete', style: TextStyle(color: Colors.redAccent))]),
                        ),
                      ],
                    ),
                  ),
                if (showOverlay)
                  Positioned(
                    bottom: 16,
                    right: 16,
                    child: GestureDetector(
                      onTap: () {
                        setState(() {
                          if (isSelected) _selectedIds.remove(docId);
                          else _selectedIds.add(docId);
                        });
                      },
                      child: Container(
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: isSelected ? Colors.blueAccent : Colors.transparent,
                          border: Border.all(color: isSelected ? Colors.blueAccent : Colors.white.withValues(alpha: 0.5), width: 2),
                        ),
                        padding: const EdgeInsets.all(2),
                        child: Icon(
                          Icons.check,
                          size: 16,
                          color: isSelected ? Colors.white : Colors.transparent,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        );
      }
    );
  }
}
