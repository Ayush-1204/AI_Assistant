import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api_client.dart';

class AuthState {
  final bool isAuthenticated;
  final String? token;
  final String? email;
  final String? name;

  AuthState({required this.isAuthenticated, this.token, this.email, this.name});
}

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiClient apiClient;

  AuthNotifier(this.apiClient) : super(AuthState(isAuthenticated: false));

  String? _decodeNameFromToken(String token) {
    try {
      final parts = token.split('.');
      if (parts.length != 3) return null;
      
      String payloadStr = parts[1];
      // Pad base64Url string if needed
      while (payloadStr.length % 4 != 0) {
        payloadStr += '=';
      }
      
      final payloadBytes = base64Url.decode(payloadStr);
      final payload = jsonDecode(utf8.decode(payloadBytes));
      return payload['name'];
    } catch (_) {
      return null;
    }
  }

  Future<void> loginWithEmail(String email, String password) async {
    final token = await apiClient.loginWithEmail(email, password);
    if (token != null) {
      apiClient.setToken(token);
      final name = _decodeNameFromToken(token);
      state = AuthState(isAuthenticated: true, token: token, email: email, name: name);
    } else {
      throw Exception('Invalid credentials');
    }
  }

  void loginWithToken(String token) {
    apiClient.setToken(token);
    final name = _decodeNameFromToken(token);
    state = AuthState(isAuthenticated: true, token: token, name: name);
  }

  Future<void> registerUser(String email, String fullName, String password) async {
    await apiClient.registerUser(email, fullName, password);
  }

  void logout() {
    apiClient.setToken(null);
    state = AuthState(isAuthenticated: false);
  }
}

// Singleton API instance shared across providers
final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.read(apiClientProvider));
});
