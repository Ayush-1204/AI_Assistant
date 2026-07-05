import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'providers/auth_provider.dart';
import 'login_view.dart';

class SettingsView extends ConsumerStatefulWidget {
  const SettingsView({super.key});

  @override
  ConsumerState<SettingsView> createState() => _SettingsViewState();
}

class _SettingsViewState extends ConsumerState<SettingsView> {
  bool _voiceBargein = true;
  bool _autoMemory = true;
  bool _isLinkingGoogle = false;

  Future<void> _handleLinkGoogle() async {
    setState(() => _isLinkingGoogle = true);
    try {
      final api = ref.read(apiClientProvider);
      // /auth/google/login requires JWT (account linking endpoint — correct for settings)
      final googleUrl = await api.getGoogleLinkUrl();
      if (googleUrl != null) {
        html.window.location.href = googleUrl;
      } else {
        _showSnack('Google OAuth is not configured on the server.');
      }
    } catch (e) {
      _showSnack('Failed to start Google linking: ${e.toString().replaceFirst("Exception: ", "")}');
    } finally {
      if (mounted) setState(() => _isLinkingGoogle = false);
    }
  }

  void _handleSignOut() {
    ref.read(authProvider.notifier).logout();
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const LoginView()),
      (_) => false,
    );
  }

  void _showSnack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: const Color(0xFF1E1E1E),
    ));
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final userEmail = authState.email ?? 'Authenticated User';

    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Profile & Settings', style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
          const SizedBox(height: 32),

          // ── Profile Card ──
          _SettingsCard(
            child: Row(
              children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor: Colors.white10,
                  child: Text(userEmail.isNotEmpty ? userEmail[0].toUpperCase() : 'U',
                    style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white)),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Text('Signed In', style: TextStyle(fontSize: 12, color: Colors.white38)),
                    Text(userEmail, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500, color: Colors.white)),
                  ]),
                ),
                OutlinedButton.icon(
                  onPressed: _handleSignOut,
                  icon: const Icon(Icons.logout, size: 16),
                  label: const Text('Sign Out'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.redAccent,
                    side: const BorderSide(color: Colors.redAccent, width: 1),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // ── Google Account Linking ──
          const Text('Connected Accounts', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _SettingsCard(
            child: Row(
              children: [
                Container(
                  width: 40, height: 40,
                  decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(8)),
                  alignment: Alignment.center,
                  child: const Text('G', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white70)),
                ),
                const SizedBox(width: 16),
                const Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('Google Account', style: TextStyle(fontWeight: FontWeight.w600)),
                    Text('Link Google to enable Calendar, Gmail & Drive features',
                      style: TextStyle(fontSize: 12, color: Colors.white38)),
                  ]),
                ),
                const SizedBox(width: 16),
                _isLinkingGoogle
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : ElevatedButton(
                        onPressed: _handleLinkGoogle,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF2D2D2D),
                          foregroundColor: Colors.white,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                            side: BorderSide(color: Colors.white.withOpacity(0.15)),
                          ),
                        ),
                        child: const Text('Connect', style: TextStyle(fontSize: 13)),
                      ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // ── AI Features ──
          const Text('AI Features', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _SettingsCard(
            child: Column(
              children: [
                _ToggleTile(
                  title: 'Voice Barge-in',
                  subtitle: 'Allow microphone to interrupt the AI while speaking',
                  value: _voiceBargein,
                  onChanged: (v) => setState(() => _voiceBargein = v),
                ),
                Divider(color: Colors.white.withOpacity(0.06)),
                _ToggleTile(
                  title: 'Auto-Extract Memories',
                  subtitle: 'Detect background details to store permanently',
                  value: _autoMemory,
                  onChanged: (v) => setState(() => _autoMemory = v),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // ── Data Management ──
          const Text('Data Management', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _SettingsCard(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.download, color: Colors.white60),
                  title: const Text('Export User Data'),
                  contentPadding: EdgeInsets.zero,
                  onTap: () => _showSnack('Export coming soon'),
                ),
                Divider(color: Colors.white.withOpacity(0.06)),
                ListTile(
                  leading: const Icon(Icons.delete_forever, color: Colors.redAccent),
                  title: const Text('Delete Account', style: TextStyle(color: Colors.redAccent)),
                  contentPadding: EdgeInsets.zero,
                  onTap: () => _showSnack('Contact support to delete your account'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SettingsCard extends StatelessWidget {
  final Widget child;
  const _SettingsCard({required this.child});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: const Color(0xFF141416).withOpacity(0.8),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white.withOpacity(0.07)),
        ),
        child: child,
      ),
    );
  }
}

class _ToggleTile extends StatelessWidget {
  final String title;
  final String subtitle;
  final bool value;
  final ValueChanged<bool> onChanged;

  const _ToggleTile({required this.title, required this.subtitle, required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return SwitchListTile(
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w500)),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 12, color: Colors.white38)),
      value: value,
      onChanged: onChanged,
      activeColor: Theme.of(context).colorScheme.primary,
      contentPadding: EdgeInsets.zero,
    );
  }
}
