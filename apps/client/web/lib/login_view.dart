import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'providers/auth_provider.dart';
import 'providers/auth_provider.dart' show apiClientProvider;
import 'layout.dart';

class LoginView extends ConsumerStatefulWidget {
  const LoginView({super.key});

  @override
  ConsumerState<LoginView> createState() => _LoginViewState();
}

class _LoginViewState extends ConsumerState<LoginView> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _fullNameController = TextEditingController();
  bool _obscurePassword = true;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _tabController.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _tabController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _fullNameController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (_emailController.text.trim().isEmpty || _passwordController.text.isEmpty) {
      setState(() => _errorMessage = 'Please enter your email and password.');
      return;
    }
    setState(() { _isLoading = true; _errorMessage = null; });
    try {
      await ref.read(authProvider.notifier).loginWithEmail(
        _emailController.text.trim(),
        _passwordController.text,
      );
      if (mounted) {
        Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const MainLayout()));
      }
    } catch (e) {
      setState(() => _errorMessage = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _handleRegister() async {
    if (_emailController.text.trim().isEmpty || _passwordController.text.isEmpty || _fullNameController.text.trim().isEmpty) {
      setState(() => _errorMessage = 'All fields are required.');
      return;
    }
    setState(() { _isLoading = true; _errorMessage = null; });
    try {
      await ref.read(authProvider.notifier).registerUser(
        _emailController.text.trim(),
        _fullNameController.text.trim(),
        _passwordController.text,
      );
      await ref.read(authProvider.notifier).loginWithEmail(
        _emailController.text.trim(),
        _passwordController.text,
      );
      if (mounted) {
        Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const MainLayout()));
      }
    } catch (e) {
      setState(() => _errorMessage = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _handleGoogleSignIn() async {
    setState(() { _isLoading = true; _errorMessage = null; });
    try {
      final api = ref.read(apiClientProvider);
      
      // Pass the current flutter port exactly so the backend can redirect back reliably
      final currentOrigin = html.window.location.origin;
      final googleUrl = await api.getGoogleInitUrl(currentOrigin);
      
      if (googleUrl != null) {
        html.window.location.href = googleUrl;
      } else {
        setState(() => _errorMessage = 'Google sign-in is not configured on the server.');
      }
    } catch (e) {
      setState(() => _errorMessage = 'Could not start Google sign-in: ${e.toString().replaceFirst("Exception: ", "")}');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      body: Stack(
        children: [
          Container(
            decoration: const BoxDecoration(
              gradient: RadialGradient(
                center: Alignment(0, -0.8),
                radius: 0.9,
                colors: [Color(0xFF232328), Color(0xFF050505)],
                stops: [0.0, 1.0],
              ),
            ),
          ),
          Center(
            child: SingleChildScrollView(
              child: Container(
                width: 440,
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 48),
                child: Column(
                  children: [
                    Container(
                      width: 48, height: 48,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.white.withOpacity(0.2)),
                        color: Colors.white.withOpacity(0.05),
                      ),
                      child: const Icon(Icons.hub_outlined, color: Colors.white, size: 22),
                    ),
                    const SizedBox(height: 16),
                    const Text('Second Brain', style: TextStyle(
                      fontSize: 28, fontWeight: FontWeight.w600,
                      color: Colors.white, letterSpacing: -0.5,
                    )),
                    const SizedBox(height: 6),
                    Text('Welcome back to your workspace', style: TextStyle(fontSize: 15, color: Colors.grey[500])),
                    const SizedBox(height: 32),
                    Container(
                      decoration: BoxDecoration(
                        color: const Color(0xFF141416).withOpacity(0.8),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: Colors.white.withOpacity(0.08)),
                        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.4), blurRadius: 40, offset: const Offset(0, 16))],
                      ),
                      child: Column(
                        children: [
                          Container(
                            decoration: BoxDecoration(
                              border: Border(bottom: BorderSide(color: Colors.white.withOpacity(0.08))),
                            ),
                            child: TabBar(
                              controller: _tabController,
                              labelColor: Colors.white,
                              unselectedLabelColor: Colors.grey[600],
                              labelStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
                              indicator: const UnderlineTabIndicator(
                                borderSide: BorderSide(color: Colors.white, width: 2),
                              ),
                              tabs: const [Tab(text: 'Log In'), Tab(text: 'Sign Up')],
                            ),
                          ),
                          Padding(
                            padding: const EdgeInsets.all(28),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                // Form fields
                                AnimatedSwitcher(
                                  duration: const Duration(milliseconds: 200),
                                  child: _tabController.index == 0
                                      ? _buildLoginForm()
                                      : _buildRegisterForm(),
                                ),
                                // Error banner
                                if (_errorMessage != null) ...[
                                  const SizedBox(height: 12),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                    decoration: BoxDecoration(
                                      color: Colors.red.withOpacity(0.1),
                                      borderRadius: BorderRadius.circular(8),
                                      border: Border.all(color: Colors.red.withOpacity(0.3)),
                                    ),
                                    child: Row(children: [
                                      const Icon(Icons.error_outline, color: Colors.redAccent, size: 16),
                                      const SizedBox(width: 8),
                                      Expanded(child: Text(_errorMessage!, style: const TextStyle(color: Colors.redAccent, fontSize: 13))),
                                    ]),
                                  ),
                                ],
                                const SizedBox(height: 20),
                                // Primary action button
                                SizedBox(
                                  height: 42,
                                  child: ElevatedButton(
                                    onPressed: _isLoading ? null : (_tabController.index == 0 ? _handleLogin : _handleRegister),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: const Color(0xFF2D2D2D),
                                      foregroundColor: Colors.white,
                                      elevation: 0,
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(8),
                                        side: BorderSide(color: Colors.white.withOpacity(0.15)),
                                      ),
                                    ),
                                    child: _isLoading
                                        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                        : Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                                            Text(_tabController.index == 0 ? 'Log In' : 'Create Account',
                                              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
                                            const SizedBox(width: 6),
                                            const Icon(Icons.arrow_forward, size: 16),
                                          ]),
                                  ),
                                ),
                                const SizedBox(height: 16),
                                Row(children: [
                                  Expanded(child: Divider(color: Colors.white.withOpacity(0.1))),
                                  Padding(
                                    padding: const EdgeInsets.symmetric(horizontal: 12),
                                    child: Text('or', style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                                  ),
                                  Expanded(child: Divider(color: Colors.white.withOpacity(0.1))),
                                ]),
                                const SizedBox(height: 16),
                                // Google sign-in — uses dart:html for Flutter Web
                                SizedBox(
                                  height: 42,
                                  child: OutlinedButton.icon(
                                    onPressed: _isLoading ? null : _handleGoogleSignIn,
                                    icon: const _GoogleIcon(),
                                    label: const Text('Continue with Google',
                                      style: TextStyle(color: Colors.white, fontSize: 14)),
                                    style: OutlinedButton.styleFrom(
                                      foregroundColor: Colors.white,
                                      side: BorderSide(color: Colors.white.withOpacity(0.1)),
                                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),
                    Text('By continuing, you agree to our Terms of Service and Privacy Policy',
                      style: TextStyle(color: Colors.grey[600], fontSize: 12), textAlign: TextAlign.center),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoginForm() {
    return Column(
      key: const ValueKey('login'),
      children: [
        _ObsidianInput(controller: _emailController, label: 'Email address', hint: 'you@example.com', icon: Icons.mail_outline, keyboardType: TextInputType.emailAddress),
        const SizedBox(height: 16),
        _ObsidianInput(controller: _passwordController, label: 'Password', hint: '••••••••', icon: Icons.lock_outline, obscureText: _obscurePassword, onToggleObscure: () => setState(() => _obscurePassword = !_obscurePassword)),
        const SizedBox(height: 4),
        Align(alignment: Alignment.centerRight, child: TextButton(onPressed: () {}, child: Text('Forgot password?', style: TextStyle(fontSize: 12, color: Colors.grey[500])))),
      ],
    );
  }

  Widget _buildRegisterForm() {
    return Column(
      key: const ValueKey('register'),
      children: [
        _ObsidianInput(controller: _fullNameController, label: 'Full name', hint: 'Your display name', icon: Icons.person_outline),
        const SizedBox(height: 14),
        _ObsidianInput(controller: _emailController, label: 'Email address', hint: 'you@example.com', icon: Icons.mail_outline, keyboardType: TextInputType.emailAddress),
        const SizedBox(height: 14),
        _ObsidianInput(controller: _passwordController, label: 'Password', hint: '••••••••', icon: Icons.lock_outline, obscureText: _obscurePassword, onToggleObscure: () => setState(() => _obscurePassword = !_obscurePassword)),
        const SizedBox(height: 4),
      ],
    );
  }
}

// ---------- Shared Components ----------

class _ObsidianInput extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final String hint;
  final IconData icon;
  final bool obscureText;
  final VoidCallback? onToggleObscure;
  final TextInputType? keyboardType;

  const _ObsidianInput({
    required this.controller, required this.label, required this.hint, required this.icon,
    this.obscureText = false, this.onToggleObscure, this.keyboardType,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(fontSize: 13, color: Colors.grey[500], fontWeight: FontWeight.w500)),
        const SizedBox(height: 6),
        TextField(
          controller: controller,
          obscureText: obscureText,
          keyboardType: keyboardType,
          style: const TextStyle(color: Color(0xFFF3F4F6), fontSize: 15),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: TextStyle(color: Colors.grey[700]),
            prefixIcon: Icon(icon, color: Colors.grey[600], size: 18),
            suffixIcon: onToggleObscure != null
                ? IconButton(icon: Icon(obscureText ? Icons.visibility : Icons.visibility_off, color: Colors.grey[600], size: 18), onPressed: onToggleObscure)
                : null,
            filled: true,
            fillColor: const Color(0xFF0A0A0C).withOpacity(0.8),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide(color: Colors.white.withOpacity(0.12))),
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide(color: Colors.white.withOpacity(0.12))),
            focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide(color: Colors.white.withOpacity(0.35))),
            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          ),
        ),
      ],
    );
  }
}

class _GoogleIcon extends StatelessWidget {
  const _GoogleIcon();
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 18, height: 18,
      alignment: Alignment.center,
      child: const Text('G', style: TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w700)),
    );
  }
}
