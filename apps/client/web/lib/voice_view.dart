import 'dart:async';
import 'dart:math' as math;
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'providers/chat_provider.dart';

double calculateRms(Uint8List pcm16Bytes) {
  if (pcm16Bytes.length < 2) return 0.0;
  final byteData = ByteData.sublistView(pcm16Bytes);
  final sampleCount = pcm16Bytes.length ~/ 2;
  if (sampleCount == 0) return 0.0;

  double sumSquares = 0;
  for (int i = 0; i < sampleCount; i++) {
    final sample = byteData.getInt16(i * 2, Endian.little);
    final normalized = sample / 32768.0;
    sumSquares += normalized * normalized;
  }
  final rms = math.sqrt(sumSquares / sampleCount);
  return math.min(1.0, rms * 4.5); // gain — tune so normal speech reads ~0.5–0.8
}

double _lerp(double a, double b, double t) => a + (b - a) * t;

class SpringValue {
  double value;
  double velocity = 0;
  final double stiffness;
  final double damping;
  SpringValue({this.value = 0, required this.stiffness, required this.damping});

  void step(double target, double dt) {
    final force = (target - value) * stiffness - velocity * damping;
    velocity += force * dt;
    value += velocity * dt;
  }
}

enum OrbState { idle, userSpeaking, aiResponding }

class VoiceOrbController extends ChangeNotifier {
  double _amplitude = 0.0;
  OrbState _state = OrbState.idle;

  double get amplitude => _amplitude;
  OrbState get state => _state;

  void pushAmplitude(double raw) {
    if (raw.isNaN) raw = 0.0;
    _amplitude = _amplitude * 0.72 + raw.clamp(0.0, 1.0) * 0.28;
    notifyListeners();
  }

  void setState(OrbState newState) {
    if (_state == newState) return;
    _state = newState;
    notifyListeners();
  }
}

class ReactiveOrbPainter extends CustomPainter {
  final double time;
  final double stretch; // 0 = compact orbiting blob, 1 = wide waveform
  final double jelly;
  final Size targetSize;

  ReactiveOrbPainter({
    required this.time,
    required this.stretch,
    required this.jelly,
    required this.targetSize,
  });

  static const cyan = Color(0xFF3FE0E8);
  static const purple = Color(0xFF9B5CFF);

  @override
  void paint(Canvas canvas, Size size) {
    // We use targetSize instead of the canvas size, so the texture doesn't churn during layout animations!
    final center = Offset(size.width / 2, size.height / 2);
    final baseRadius = targetSize.height * 0.42;

    // orbit path: near-circular when idle -> wide flat horizontal ellipse when stretched
    final orbitX = _lerp(baseRadius * 0.30, targetSize.width * 0.5 - baseRadius * 0.5, stretch);
    final orbitY = _lerp(baseRadius * 0.30, baseRadius * 0.04, stretch);

    // AI-response pulse: fast breathing on lobe size, independent of stretch
    final jellyPulse = 1 + jelly.clamp(-0.3, 1.2) * 0.30;
    final lobeRadius = baseRadius * (1.0 - stretch * 0.15) * jellyPulse;

    final angle = time * 0.5; // slow continuous orbit -> the "living" swirl

    final posA = center + Offset(math.cos(angle) * orbitX, math.sin(angle) * orbitY);
    final posB = center + Offset(math.cos(angle + math.pi) * orbitX, math.sin(angle + math.pi) * orbitY);

    // soft outer ambient glow
    canvas.drawCircle(
      center,
      baseRadius * 2.0,
      Paint()
        ..shader = RadialGradient(colors: [purple.withValues(alpha: 0.25), Colors.transparent])
            .createShader(Rect.fromCircle(center: center, radius: baseRadius * 2.2))
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 30),
    );

    void drawLobe(Offset pos, Color color) {
      canvas.drawCircle(
        pos,
        lobeRadius,
        Paint()
          ..shader = RadialGradient(
            colors: [Colors.white, color, color.withValues(alpha: 0.0)],
            stops: const [0.0, 0.45, 1.0],
          ).createShader(Rect.fromCircle(center: pos, radius: lobeRadius))
          ..blendMode = BlendMode.plus // overlap glows white-hot, matches reference core
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10),
      );
    }

    drawLobe(posA, cyan);
    drawLobe(posB, purple);
  }

  @override
  bool shouldRepaint(covariant ReactiveOrbPainter old) =>
      old.time != time || old.stretch != stretch || old.jelly != jelly || old.targetSize != targetSize;
}

class ReactiveVoiceOrb extends StatefulWidget {
  final VoiceOrbController controller;
  const ReactiveVoiceOrb({super.key, required this.controller});

  @override
  State<ReactiveVoiceOrb> createState() => _ReactiveVoiceOrbState();
}

class _ReactiveVoiceOrbState extends State<ReactiveVoiceOrb> with SingleTickerProviderStateMixin {
  late final Ticker _ticker;
  Duration _last = Duration.zero;
  double _time = 0.0;

  final _stretchSpring = SpringValue(stiffness: 90, damping: 14);  // slower, more liquid unfurl
  final _jellySpring = SpringValue(stiffness: 260, damping: 13);   // fast, punchy pulse

  @override
  void initState() {
    super.initState();
    _ticker = createTicker(_onTick)..start();
    widget.controller.addListener(_triggerPaint);
  }

  void _triggerPaint() {
    setState(() {}); // Repaint intentionally from provider amplitude pushes
  }

  void _onTick(Duration elapsed) {
    final dt = ((elapsed - _last).inMicroseconds / 1e6).clamp(0.0, 0.05);
    _last = elapsed;
    _time += dt;

    final state = widget.controller.state;
    final amp = widget.controller.amplitude;

    final stretchTarget = state == OrbState.userSpeaking ? (0.35 + amp * 0.65) : 0.0;
    final jellyTarget = state == OrbState.aiResponding ? amp : 0.0;

    _stretchSpring.step(stretchTarget, dt);
    _jellySpring.step(jellyTarget, dt);

    setState(() {});
  }

  @override
  void dispose() {
    widget.controller.removeListener(_triggerPaint);
    _ticker.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return OverflowBox(
          minWidth: 400, maxWidth: 400,
          minHeight: 240, maxHeight: 240,
          child: CustomPaint(
            size: const Size(400, 240),
            painter: ReactiveOrbPainter(
              time: _time,
              stretch: _stretchSpring.value.clamp(0.0, 1.0),
              jelly: _jellySpring.value,
              targetSize: Size(constraints.maxWidth, constraints.maxHeight),
            ),
          ),
        );
      },
    );
  }
}

class VoiceModeView extends ConsumerStatefulWidget {
  const VoiceModeView({super.key});

  @override
  ConsumerState<VoiceModeView> createState() => _VoiceModeViewState();
}

class _VoiceModeViewState extends ConsumerState<VoiceModeView> {
  final VoiceOrbController _orbController = VoiceOrbController();
  Timer? _ttsJitterTimer;

  void _onAudioChunk(Uint8List pcm, bool isTts) {
    final rms = calculateRms(pcm);
    if (isTts && _orbController.state == OrbState.aiResponding) {
      // Must be playing TTS audio and state properly matches
      _orbController.pushAmplitude(rms);
    } else if (!isTts && _orbController.state == OrbState.userSpeaking) {
      // Must be capturing mic audio and state properly matches
      _orbController.pushAmplitude(rms);
    }
  }

  @override
  void initState() {
    super.initState();
  }

  @override
  void dispose() {
    _ttsJitterTimer?.cancel();
    _orbController.dispose();
    super.dispose();
  }

  void _handleInterrupt(ChatNotifier provider, ChatState state) {
    if (state.isSpeaking || state.isProcessing) {
       provider.stopSpeaking();
    } else if (state.isListening || state.isVoiceTyping) {
       provider.stopListening();
    } else {
       // User explicitly toggles listening while idle
       provider.toggleVoiceTyping(); // or toggleListening depending on continuous tracking
    }
  }

  void _syncOrbState(ChatState state) {
    if (state.isSpeaking) {
      _orbController.setState(OrbState.aiResponding);
      // Spawn spoof TTS jitter if none exists
      if (_ttsJitterTimer == null || !_ttsJitterTimer!.isActive) {
        _ttsJitterTimer = Timer.periodic(const Duration(milliseconds: 60), (timer) {
          if (!ref.read(chatProvider).isSpeaking) {
            timer.cancel();
          } else {
             // TTS synthetic RMS
             final syntheticRms = math.Random().nextDouble() * 0.4 + 0.5;
             _orbController.pushAmplitude(syntheticRms);
          }
        });
      }
    } else if (state.isListening || state.isVoiceTyping) {
      _orbController.setState(OrbState.userSpeaking);
      _ttsJitterTimer?.cancel();
    } else if (state.isProcessing) {
      _orbController.setState(OrbState.idle); // "keep waveform, low amplitude, feels like thinking" 
      _ttsJitterTimer?.cancel();
    } else {
      _orbController.setState(OrbState.idle);
      _ttsJitterTimer?.cancel();
    }
  }

  @override
  Widget build(BuildContext context) {
    // Sync Riverpod state down to the local controller whenever state rebuilds.
    final state = ref.watch(chatProvider);
    final provider = ref.read(chatProvider.notifier);

    // Voice Mode Lifecycle & Listeners
    ref.listen(chatProvider, (prev, next) {
      if (next.shouldAutoExitVoiceMode && (prev == null || !prev.shouldAutoExitVoiceMode)) {
        provider.resetVoiceExit();
        provider.setContinuousVoiceMode(false);
      }
      
      final wasVoiceMode = prev?.isContinuousVoiceMode ?? false;
      final isVoiceMode = next.isContinuousVoiceMode;
      
      if (isVoiceMode && !wasVoiceMode) {
        provider.setVoiceModeExpanded(true); // Start expanded
        provider.addMessage("System: — Voice Mode Activated —");
        provider.setAudioChunkCallback(_onAudioChunk);
        if (!next.isListening && !next.isVoiceTyping) {
          provider.toggleVoiceTyping(); // Auto-start listening!
        }
      } else if (!isVoiceMode && wasVoiceMode) {
        provider.addMessage("System: — Voice Mode Ended —");
        provider.setAudioChunkCallback(null);
      }
    });
    
    // Defer state sync safely out of build phase
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _syncOrbState(state);
    });
    
    String statusText = "";
    if (state.isListening || state.isVoiceTyping) {
      statusText = "Listening...";
    } else if (state.isProcessing) {
      statusText = "Thinking...";
    } else if (state.isSpeaking) {
      statusText = "Speaking...";
    }

    // No early return so animations can play!

    return Positioned.fill(
      child: Stack(
        children: [
          // Dim background for expanded mode
          IgnorePointer(
            ignoring: !(state.isVoiceModeExpanded && state.isContinuousVoiceMode),
            child: GestureDetector(
              onTap: () => provider.setVoiceModeExpanded(false),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 700),
                curve: Curves.easeOutQuint,
                color: (state.isVoiceModeExpanded && state.isContinuousVoiceMode) ? Colors.black.withValues(alpha: 0.85) : Colors.transparent,
              ),
            ),
          ),
          
          // Expanded UI Elements (Close button)
          Positioned(
            top: 16,
            left: 16,
            child: SafeArea(
              child: IgnorePointer(
                ignoring: !(state.isVoiceModeExpanded && state.isContinuousVoiceMode),
                child: AnimatedOpacity(
                  duration: const Duration(milliseconds: 400),
                  curve: Curves.easeOut,
                  opacity: (state.isVoiceModeExpanded && state.isContinuousVoiceMode) ? 1.0 : 0.0,
                  child: IconButton(
                    icon: const Icon(Icons.close, color: Colors.white70),
                    onPressed: () {
                      provider.setContinuousVoiceMode(false);
                      if (state.isSpeaking) provider.stopSpeaking();
                      if (state.isListening || state.isVoiceTyping) provider.stopListening();
                    },
                  ),
                ),
              ),
            ),
          ),

          // Blob Container
          Positioned.fill(
            child: AnimatedAlign(
              duration: const Duration(milliseconds: 2500),
              curve: Curves.easeInCubic,
              alignment: state.isVoiceModeExpanded ? Alignment.center : const Alignment(0, 0.75),
              child: IgnorePointer(
                ignoring: !state.isContinuousVoiceMode,
                child: GestureDetector(
                  onTap: () {
                    provider.setVoiceModeExpanded(!state.isVoiceModeExpanded);
                  },
                child: AnimatedOpacity(
                  duration: const Duration(milliseconds: 400),
                  opacity: state.isContinuousVoiceMode ? 1.0 : 0.0,
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 2500),
                    curve: Curves.easeInCubic,
                    width: !state.isContinuousVoiceMode ? 0 : (state.isVoiceModeExpanded ? 400 : 80),
                    height: !state.isContinuousVoiceMode ? 0 : (state.isVoiceModeExpanded ? 240 : 80),
                    child: ReactiveVoiceOrb(
                      controller: _orbController,
                    ),
                  ),
                  ),
                ),
              ),
            ),
          ),
          // Status Text
          Align(
            alignment: const Alignment(0, 0.35),
            child: IgnorePointer(
              ignoring: !(state.isVoiceModeExpanded && state.isContinuousVoiceMode),
              child: AnimatedOpacity(
                duration: const Duration(milliseconds: 400),
                curve: Curves.easeOut,
                opacity: (state.isVoiceModeExpanded && state.isContinuousVoiceMode && statusText.isNotEmpty) ? 1.0 : 0.0,
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 300),
                  child: Text(
                    statusText,
                    key: ValueKey<String>(statusText),
                    style: const TextStyle(
                      color: Colors.white38,
                      fontSize: 16,
                      fontWeight: FontWeight.w400,
                      letterSpacing: 1.5,
                    ),
                  ),
                ),
              ),
            ),
          ),
            
          // Live Transcript
          Align(
            alignment: Alignment.bottomCenter,
            child: IgnorePointer(
              ignoring: !(state.isVoiceModeExpanded && state.isContinuousVoiceMode),
              child: AnimatedOpacity(
                duration: const Duration(milliseconds: 400),
                curve: Curves.easeOut,
                opacity: (state.isVoiceModeExpanded && state.isContinuousVoiceMode) ? 1.0 : 0.0,
                child: AnimatedSlide(
                  duration: const Duration(milliseconds: 600),
                  curve: Curves.easeOutQuint,
                  offset: (state.isVoiceModeExpanded && state.isContinuousVoiceMode) ? Offset.zero : const Offset(0, 0.2),
                  child: Container(
                    height: 250,
                    padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 20),
                    child: ShaderMask(
                      shaderCallback: (Rect bounds) {
                        return const LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [Colors.transparent, Colors.black, Colors.black],
                          stops: [0.0, 0.35, 1.0],
                        ).createShader(bounds);
                      },
                      blendMode: BlendMode.dstIn,
                      child: ListView(
                        reverse: true,
                        children: [
                          if (state.liveTranscript.isNotEmpty)
                            Padding(
                              padding: const EdgeInsets.only(top: 16),
                              child: Text(
                                state.liveTranscript,
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 18,
                                  height: 1.4,
                                  fontWeight: FontWeight.w300,
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
