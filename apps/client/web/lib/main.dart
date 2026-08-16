import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter/gestures.dart';
import 'login_view.dart';
import 'layout.dart';
import 'providers/auth_provider.dart';

class _AppScrollBehavior extends MaterialScrollBehavior {
  @override
  Set<PointerDeviceKind> get dragDevices => {
        PointerDeviceKind.touch,
        PointerDeviceKind.trackpad,
      };
}

void main() {
  runApp(const ProviderScope(child: SecondBrainApp()));
}

class SecondBrainApp extends StatelessWidget {
  const SecondBrainApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Second Brain AI',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      scrollBehavior: _AppScrollBehavior(),
      darkTheme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFFFFFFFF),    // Noir Primary
          secondary: Color(0xFFCCCCCC),  // Noir Secondary
          surface: Color(0xFF131313), // Noir Background
          onPrimary: Color(0xFF000000),  // text on primary
          onSurface: Color(0xFFF5F5F5),
          error: Color(0xFFFFB4AB),
        ),
        textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
        scaffoldBackgroundColor: Colors.black,
      ),
      home: const LoginView(),
      onGenerateRoute: (settings) {
        if (settings.name != null && settings.name!.startsWith('/auth/callback')) {
          final uri = Uri.parse(settings.name!);
          final token = uri.queryParameters['token'];

          if (token != null) {
            return MaterialPageRoute(
              builder: (context) => OAuthCallbackHandler(token: token),
            );
          }
        }
        return null;
      },
    );
  }
}

class OAuthCallbackHandler extends ConsumerWidget {
  final String token;
  const OAuthCallbackHandler({super.key, required this.token});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(authProvider.notifier).loginWithToken(token);
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const MainLayout()),
      );
    });
    return const Scaffold(
      backgroundColor: Color(0xFF0F172A),
      body: Center(
        child: CircularProgressIndicator(color: Colors.white),
      ),
    );
  }
}
