import 'dart:typed_data';

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:dio/dio.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class ApiClient {
  static const String baseUrl = 'http://localhost:8000';
  final Dio _dio;
  String? _authToken;
  double? _lat;
  double? _lon;
  bool _isLocalOnly = false;
  http.Client? _activeStreamClient;

  ApiClient() : _dio = Dio(BaseOptions(baseUrl: baseUrl)) {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        if (_authToken != null) {
          options.headers['Authorization'] = 'Bearer $_authToken';
        }
        if (_lat != null && _lon != null) {
          options.headers['X-User-Lat'] = _lat.toString();
          options.headers['X-User-Lon'] = _lon.toString();
        }
        if (_isLocalOnly) {
          options.headers['X-Local-Only'] = 'True';
        }
        return handler.next(options);
      },
    ));
  }

  void setToken(String? token) {
    _authToken = token;
  }

  String? get token => _authToken;

  void setLocation(double lat, double lon) {
    _lat = lat;
    _lon = lon;
  }

  void setLocalOnly(bool value) {
    _isLocalOnly = value;
  }

  bool get isLocalOnly => _isLocalOnly;
  bool get isAuthenticated => _authToken != null;

  /// POST /auth/login — uses OAuth2PasswordRequestForm (x-www-form-urlencoded)
  /// Backend uses `username` field to accept email
  Future<String?> loginWithEmail(String email, String password) async {
    try {
      final response = await _dio.post(
        '/auth/login',
        data: 'username=${Uri.encodeComponent(email)}&password=${Uri.encodeComponent(password)}',
        options: Options(
          contentType: 'application/x-www-form-urlencoded',
        ),
      );
      return response.data['access_token'];
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Login failed');
    }
  }

  /// POST /auth/register — JSON body: {email, full_name, password}
  Future<void> registerUser(String email, String fullName, String password) async {
    try {
      await _dio.post('/auth/register', data: {
        'email': email,
        'full_name': fullName,
        'password': password,
      });
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Registration failed');
    }
  }

  /// GET /auth/google/init — PUBLIC, no JWT required. Returns Google consent URL.
  Future<String?> getGoogleInitUrl([String? frontendUrl]) async {
    try {
      final queryStr = frontendUrl != null ? '?frontend_url=${Uri.encodeComponent(frontendUrl)}' : '';
      final response = await _dio.get('/auth/google/init$queryStr');
      return response.data['authorization_url'];
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Failed to get Google auth URL');
    }
  }

  /// GET /auth/google/login — JWT required. Used by Settings to link Google to existing account.
  Future<String?> getGoogleLinkUrl() async {
    try {
      final response = await _dio.get('/auth/google/login');
      return response.data['authorization_url'];
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Failed to get Google link URL');
    }
  }

  Future<List<dynamic>> fetchNotes() async {
    try {
      final response = await _dio.get('/notes');
      return response.data['data'] ?? [];
    } catch (_) {
      return [];
    }
  }



  Future<void> uploadDocument(String title, List<int> bytes, String filename) async {
    try {
      final formData = FormData.fromMap({
        'title': title,
        'file': MultipartFile.fromBytes(bytes, filename: filename),
      });
      await _dio.post(
        '/documents/upload',
        data: formData,
      );
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Document upload failed');
    }
  }

  Future<List<dynamic>> fetchDocuments() async {
    try {
      final response = await _dio.get('/documents');
      return response.data['data'] ?? [];
    } catch (_) {
      return [];
    }
  }



  Future<List<dynamic>> fetchMemories() async {
    try {
      final response = await _dio.get('/memory');
      return response.data as List<dynamic>;
    } catch (_) {
      return [];
    }
  }

  Future<List<dynamic>> fetchTasks() async {
    try {
      final response = await _dio.get('/tasks');
      return response.data as List<dynamic>;
    } catch (_) {
      return [];
    }
  }

  Future<dynamic> createTask(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post('/tasks', data: data);
      return response.data;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Create task failed');
    }
  }

  Future<void> updateTaskStatus(String taskId, String status) async {
    try {
      await _dio.put('/tasks/$taskId', data: {'status': status});
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Update task failed');
    }
  }

  Future<void> deleteTask(String taskId) async {
    try {
      await _dio.delete('/tasks/$taskId');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Delete task failed');
    }
  }

  Future<Map<String, dynamic>> fetchConversation(int conversationId) async {
    try {
      final response = await _dio.get('/conversations/$conversationId');
      return response.data as Map<String, dynamic>;
    } catch (_) {
      return {};
    }
  }

  Future<List<dynamic>> fetchConversations() async {
    try {
      final response = await _dio.get('/conversations');
      return response.data as List<dynamic>;
    } catch (_) {
      return [];
    }
  }



  Future<List<dynamic>> fetchDashboardWidgets() async {
    try {
      final response = await _dio.get('/dashboard/widgets');
      return response.data['widgets'] ?? [];
    } catch (_) {
      return [];
    }
  }

  Future<List<dynamic>> fetchCalendarEvents({int? year, int? month}) async {
    try {
      String path = '/dashboard/calendar/events';
      if (year != null && month != null) {
        path += '?year=$year&month=$month';
      }
      final response = await _dio.get(path);
      return response.data['events'] ?? [];
    } catch (_) {
      return [];
    }
  }

  Future<void> createCalendarEvent(String summary, String description, String startTime, String endTime) async {
    try {
      await _dio.post('/dashboard/calendar/events', data: {
        'summary': summary,
        'description': description,
        'start_time': startTime,
        'end_time': endTime,
      });
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Failed to create event');
    }
  }

  Future<void> deleteCalendarEvent(String eventId) async {
    try {
      await _dio.delete('/dashboard/calendar/events/$eventId');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Failed to delete event');
    }
  }

  Future<int> createConversation(String title) async {
    try {
      final response = await _dio.post('/conversations', data: {'title': title});
      return response.data['id'] as int;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Failed to create conversation');
    }
  }

  Future<void> updateConversationTitle(int id, String newTitle) async {
    try {
      await _dio.patch('/conversations/$id', data: {'title': newTitle});
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Failed to update conversation title');
    }
  }

  Future<String?> generateConversationTitle(int id, String aiResponse) async {
    try {
      final response = await _dio.post('/conversations/$id/generate-title', data: {'ai_response': aiResponse});
      return response.data['title'] as String?;
    } on DioException {
      // Non-fatal, just return null if it fails
      return null;
    }
  }

  Future<void> truncateConversation(int conversationId, int fromIndex) async {
    try {
      await _dio.post('/conversations/$conversationId/truncate', data: {'from_index': fromIndex});
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Failed to truncate conversation');
    }
  }


  Future<void> updateConversationPin(int conversationId, bool isPinned) async {
    try {
      await _dio.patch('/conversations/$conversationId', data: {'is_pinned': isPinned});
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Failed to update conversation pin');
    }
  }

  Future<void> deleteConversation(int conversationId) async {
    try {
      await _dio.delete('/conversations/$conversationId');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Failed to delete conversation');
    }
  }

  WebSocketChannel connectToVoiceStream(String conversationId) {
    final tokenParam = _authToken != null ? '?token=${Uri.encodeComponent(_authToken!)}' : '';
    final wsUrl = Uri.parse('ws://localhost:8000/voice/$conversationId$tokenParam');
    return WebSocketChannel.connect(wsUrl);
  }

  WebSocketChannel connectToDictationStream() {
    final tokenParam = _authToken != null ? '?token=${Uri.encodeComponent(_authToken!)}' : '';
    final wsUrl = Uri.parse('ws://localhost:8000/voice/dictate$tokenParam');
    return WebSocketChannel.connect(wsUrl);
  }

  Future<Uint8List> textToSpeech(String text) async {
    try {
      final response = await _dio.post(
        '/voice/tts',
        data: {'text': text},
        options: Options(responseType: ResponseType.bytes),
      );
      // Backend returns a fully-buffered MP3 response
      final data = response.data;
      if (data is Uint8List) return data;
      if (data is List<int>) return Uint8List.fromList(data);
      throw Exception('Unexpected TTS response type: ${data.runtimeType}');
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'TTS request failed');
    }
  }

  Future<String> transcribeAudio(List<int> bytes) async {
    try {
      final formData = FormData.fromMap({
        'file': MultipartFile.fromBytes(bytes, filename: 'audio.webm'),
      });
      final response = await _dio.post(
        '/voice/transcribe',
        data: formData,
      );
      return response.data['text'] ?? '';
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'STT request failed');
    }
  }

  Future<Map<String, dynamic>> sendChatMessage(String conversationId, String message, {bool isRegenerate = false, List<String>? images}) async {
    try {
      final intId = int.tryParse(conversationId) ?? (throw Exception("Invalid Conversation ID"));
      
      final Map<String, dynamic> data = {
        'conversation_id': intId, 
        'message': message,
        'is_regenerate': isRegenerate,
      };
      
      if (images != null && images.isNotEmpty) {
         data['images'] = images;
      }
      
      final response = await _dio.post(
        '/chat',
        data: data,
      );
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Chat request failed');
    }
  }

  Stream<String> sendChatMessageStream(String conversationId, String message, {bool isRegenerate = false, List<String>? images}) async* {
    final intId = int.tryParse(conversationId) ?? (throw Exception("Invalid Conversation ID"));
    
    final Map<String, dynamic> payload = {
      'conversation_id': intId, 
      'message': message,
      'is_regenerate': isRegenerate,
    };
    
    if (images != null && images.isNotEmpty) {
       payload['images'] = images;
    }
    
    final request = http.Request('POST', Uri.parse('$baseUrl/chat/stream'));
    if (_authToken != null) {
       request.headers['Authorization'] = 'Bearer $_authToken';
    }
    if (_lat != null) request.headers['X-User-Lat'] = _lat.toString();
    if (_lon != null) request.headers['X-User-Lon'] = _lon.toString();
    request.headers['Content-Type'] = 'application/json';
    request.headers['Accept'] = 'text/event-stream';
    request.headers['Cache-Control'] = 'no-cache';
    request.body = jsonEncode(payload);

    _activeStreamClient?.close();
    _activeStreamClient = http.Client();

    try {
      final response = await _activeStreamClient!.send(request);
      if (response.statusCode != 200) {
          final err = await response.stream.bytesToString();
          throw Exception("Stream failed: $err");
      }

      String buffer = "";
      await for (final chunk in response.stream) {
        buffer += utf8.decode(chunk, allowMalformed: true);
        while (buffer.contains('\n\n')) {
          int index = buffer.indexOf('\n\n');
          String block = buffer.substring(0, index).trim();
          buffer = buffer.substring(index + 2);
          
          for (var line in block.split('\n')) {
             line = line.trim();
             if (line.startsWith('data: ')) {
                 yield line.substring(6);
             }
          }
        }
      }
    } finally {
      _activeStreamClient?.close();
      _activeStreamClient = null;
    }
  }

  void abortChatStream() {
    _activeStreamClient?.close();
    _activeStreamClient = null;
  }

  /// POST /chat/approve-plan — executes approved tool steps and streams back the final response
  Stream<String> approvePlanStream(int conversationId, List<Map<String, dynamic>> approvedSteps) async* {
    final payload = {
      'conversation_id': conversationId,
      'approved_steps': approvedSteps,
    };

    final request = http.Request('POST', Uri.parse('$baseUrl/chat/approve-plan'));
    if (_authToken != null) request.headers['Authorization'] = 'Bearer $_authToken';
    request.headers['Content-Type'] = 'application/json';
    request.headers['Accept'] = 'text/event-stream';
    request.body = jsonEncode(payload);

    _activeStreamClient?.close();
    _activeStreamClient = http.Client();
    try {
      final response = await _activeStreamClient!.send(request);
      if (response.statusCode != 200) {
        final err = await response.stream.bytesToString();
        throw Exception('approve-plan failed: $err');
      }
      String buffer = '';
      await for (final chunk in response.stream) {
        buffer += utf8.decode(chunk, allowMalformed: true);
        while (buffer.contains('\n\n')) {
          final idx = buffer.indexOf('\n\n');
          final block = buffer.substring(0, idx).trim();
          buffer = buffer.substring(idx + 2);
          for (var line in block.split('\n')) {
            line = line.trim();
            if (line.startsWith('data: ')) yield line.substring(6);
          }
        }
      }
    } finally {
      _activeStreamClient?.close();
      _activeStreamClient = null;
    }
  }

  // ── Scheduled Tasks ──────────────────────────────────────────────────────
  Future<List<dynamic>> fetchScheduledTasks() async {
    try {
      final response = await _dio.get('/scheduled-tasks');
      return response.data as List<dynamic>;
    } catch (_) {
      return [];
    }
  }

  Future<dynamic> createScheduledTask({
    required String label,
    required String directive,
    String? cronExpression,
    DateTime? runAt,
    DateTime? endRepeatAt,
  }) async {
    final body = {
      'label': label,
      'directive': directive,
      if (cronExpression != null) 'cron_expression': cronExpression,
      if (runAt != null) 'run_at': runAt.toUtc().toIso8601String(),
      if (endRepeatAt != null) 'end_repeat_at': endRepeatAt.toUtc().toIso8601String(),
      'timezone_offset_minutes': DateTime.now().timeZoneOffset.inMinutes,
    };
    final response = await _dio.post('/scheduled-tasks', data: body);
    return response.data;
  }

  Future<dynamic> updateScheduledTask({
    required int id,
    String? label,
    String? directive,
    String? cronExpression,
    DateTime? runAt,
    DateTime? endRepeatAt,
  }) async {
    final body = {
      if (label != null) 'label': label,
      if (directive != null) 'directive': directive,
      if (cronExpression != null) 'cron_expression': cronExpression,
      if (runAt != null) 'run_at': runAt.toUtc().toIso8601String(),
      if (endRepeatAt != null) 'end_repeat_at': endRepeatAt.toUtc().toIso8601String(),
      'timezone_offset_minutes': DateTime.now().timeZoneOffset.inMinutes,
    };
    final response = await _dio.patch('/scheduled-tasks/$id', data: body);
    return response.data;
  }

  Future<void> deleteScheduledTask(int id) async {
    await _dio.delete('/scheduled-tasks/$id');
  }

  Future<dynamic> toggleScheduledTask(int id) async {
    final response = await _dio.patch('/scheduled-tasks/$id/toggle');
    return response.data;
  }
}


