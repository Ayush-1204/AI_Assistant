import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'auth_provider.dart';

class GreetingState {
  final String greeting;
  final String prompt;
  
  GreetingState(this.greeting, this.prompt);
}

class GreetingNotifier extends StateNotifier<GreetingState> {
  final Ref ref;
  Timer? _timer;

  GreetingNotifier(this.ref) : super(GreetingState("", "")) {
    _generate();
    // Refresh every hour
    _timer = Timer.periodic(const Duration(hours: 1), (_) {
      _generate();
    });
    
    // Regenerate if user name changes (i.e., on login)
    ref.listen(authProvider, (previous, next) {
      if (previous?.name != next.name) {
        _generate();
      }
    });
  }

  void _generate() {
    final authState = ref.read(authProvider);
    final String rawName = authState.name ?? "User";
    final String firstName = rawName.split(" ").first;
    
    final greetings = [
      "Greetings, $firstName.",
      "Welcome back, $firstName.",
      "Good to see you, $firstName.",
      "Hello there, $firstName.",
      "Hope you're having a great day, $firstName.",
      "Always a pleasure, $firstName.",
      "Nice to see you again, $firstName.",
      "Hey $firstName, ready to dive in?",
      "Good morning, $firstName.",
      "How's it going, $firstName?",
    ];
    greetings.shuffle();
    
    final prompts = [
      "What's on your mind today?",
      "How can I assist you?",
      "What would you like to explore?",
      "Let me know how I can help.",
      "What's the plan for today?",
      "Ready for your next question.",
      "What should we look into today?",
      "Feel free to ask me anything.",
      "How can I make your day easier?",
      "Is there anything specific you need?",
    ];
    prompts.shuffle();
    
    state = GreetingState(greetings.first, prompts.first);
  }
  
  // Force a regeneration (e.g. on manual login)
  void regenerate() {
    _generate();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
}

final greetingProvider = StateNotifierProvider<GreetingNotifier, GreetingState>((ref) {
  return GreetingNotifier(ref);
});
