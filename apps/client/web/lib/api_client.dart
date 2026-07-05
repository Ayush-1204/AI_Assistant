import 'package:dio/dio.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class ApiClient {
  static const String baseUrl = 'http://localhost:8000';
  final Dio _dio;
  String? _authToken;

  ApiClient() : _dio = Dio(BaseOptions(baseUrl: baseUrl)) {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        if (_authToken != null) {
          options.headers['Authorization'] = 'Bearer $_authToken';
        }
        return handler.next(options);
      },
    ));
  }

  void setToken(String? token) {
    _authToken = token;
  }

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

  Future<int> createConversation(String title) async {
    try {
      final response = await _dio.post('/conversations', data: {'title': title});
      return response.data['id'] as int;
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Failed to create conversation');
    }
  }

  WebSocketChannel connectToVoiceStream(String conversationId) {
    final wsUrl = Uri.parse('ws://localhost:8000/voice/$conversationId');
    return WebSocketChannel.connect(wsUrl);
  }

  Future<String> sendChatMessage(String conversationId, String message) async {
    try {
      final intId = int.tryParse(conversationId) ?? (throw Exception("Invalid Conversation ID"));
      final response = await _dio.post(
        '/chat',
        data: {
          'conversation_id': intId, 
          'message': message
        },
      );
      return response.data['response'] ?? '';
    } on DioException catch (e) {
      throw Exception(e.response?.data?['detail'] ?? 'Chat request failed');
    }
  }
}
