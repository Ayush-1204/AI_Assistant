import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api_client.dart';

class AuthState {
  final bool isAuthenticated;
  final String? token;
  final String? email;

  AuthState({required this.isAuthenticated, this.token, this.email});
}

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiClient apiClient;

  AuthNotifier(this.apiClient) : super(AuthState(isAuthenticated: false));

  Future<void> loginWithEmail(String email, String password) async {
    final token = await apiClient.loginWithEmail(email, password);
    if (token != null) {
      apiClient.setToken(token);
      state = AuthState(isAuthenticated: true, token: token, email: email);
    } else {
      throw Exception('Invalid credentials');
    }
  }

  void loginWithToken(String token) {
    apiClient.setToken(token);
    state = AuthState(isAuthenticated: true, token: token);
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
