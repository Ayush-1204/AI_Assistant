// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:record/record.dart';
import 'package:audioplayers/audioplayers.dart';

class AudioDebugView extends StatefulWidget {
  const AudioDebugView({super.key});

  @override
  State<AudioDebugView> createState() => _AudioDebugViewState();
}

class _AudioDebugViewState extends State<AudioDebugView> {
  final AudioRecorder _audioRecorder = AudioRecorder();
  final AudioPlayer _audioPlayer = AudioPlayer();
  
  bool _isRecording = false;
  bool _isPlaying = false;
  
  StreamSubscription<Uint8List>? _recordSub;
  final List<int> _audioBuffer = [];
  Uint8List? _lastWavBytes;
  
  @override
  void initState() {
    super.initState();
    _audioPlayer.onPlayerStateChanged.listen((state) {
      if (mounted) {
        setState(() {
          _isPlaying = state == PlayerState.playing;
        });
      }
    });
  }
  
  @override
  void dispose() {
    _recordSub?.cancel();
    _audioRecorder.dispose();
    _audioPlayer.dispose();
    super.dispose();
  }

  Uint8List _addWavHeader(Uint8List rawVoiceData) {
    final header = ByteData(44);
    final numChannels = 1;
    final sampleRate = 48000;
    final bitsPerSample = 16;
    final byteRate = (sampleRate * numChannels * bitsPerSample) ~/ 8;
    final blockAlign = (numChannels * bitsPerSample) ~/ 8;
    final dataSize = rawVoiceData.length;
    final fileSize = dataSize + 36;

    // "RIFF"
    header.setUint8(0, 0x52); header.setUint8(1, 0x49); header.setUint8(2, 0x46); header.setUint8(3, 0x46);
    header.setUint32(4, fileSize, Endian.little);
    // "WAVE"
    header.setUint8(8, 0x57); header.setUint8(9, 0x41); header.setUint8(10, 0x56); header.setUint8(11, 0x45);
    // "fmt "
    header.setUint8(12, 0x66); header.setUint8(13, 0x6D); header.setUint8(14, 0x74); header.setUint8(15, 0x20);
    header.setUint32(16, 16, Endian.little); // chunk size
    header.setUint16(20, 1, Endian.little); // PCM format
    header.setUint16(22, numChannels, Endian.little);
    header.setUint32(24, sampleRate, Endian.little);
    header.setUint32(28, byteRate, Endian.little);
    header.setUint16(32, blockAlign, Endian.little);
    header.setUint16(34, bitsPerSample, Endian.little);
    
    // "data"
    header.setUint8(36, 0x64); header.setUint8(37, 0x61); header.setUint8(38, 0x74); header.setUint8(39, 0x61);
    header.setUint32(40, dataSize, Endian.little);
    
    final out = BytesBuilder();
    out.add(header.buffer.asUint8List());
    out.add(rawVoiceData);
    return out.toBytes();
  }

  Future<void> _toggleRecord() async {
    if (_isRecording) {
      // STOP recording
      _recordSub?.cancel();
      await _audioRecorder.stop();
      
      if (_audioBuffer.isNotEmpty) {
        final rawBytes = Uint8List.fromList(_audioBuffer);
        _lastWavBytes = _addWavHeader(rawBytes);
      }
      
      setState(() {
        _isRecording = false;
      });
    } else {
      // START recording
      if (await _audioRecorder.hasPermission()) {
        final stream = await _audioRecorder.startStream(const RecordConfig(
          encoder: AudioEncoder.pcm16bits,
          sampleRate: 48000,
          numChannels: 1,
          echoCancel: true,
          autoGain: true,
          noiseSuppress: true,
        ));
        
        _audioBuffer.clear();
        setState(() {
          _isRecording = true;
          _lastWavBytes = null;
        });
        
        _recordSub = stream.listen((data) {
          _audioBuffer.addAll(data);
        });
      }
    }
  }
  
  Future<void> _togglePlay() async {
    if (_isPlaying) {
      await _audioPlayer.stop();
    } else {
      if (_lastWavBytes != null) {
        await _audioPlayer.play(BytesSource(_lastWavBytes!));
      }
    }
  }

  void _downloadWav() {
    if (_lastWavBytes == null) return;
    
    final blob = html.Blob([_lastWavBytes!]);
    final url = html.Url.createObjectUrlFromBlob(blob);
    final anchor = html.AnchorElement(href: url)
      ..setAttribute("download", "debug_recording_${DateTime.now().millisecondsSinceEpoch}.wav")
      ..click();
      
    html.Url.revokeObjectUrl(url);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: Padding(
        padding: const EdgeInsets.all(40.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
             Text("Audio Sandbox", style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white.withValues(alpha: 0.9))),
             const SizedBox(height: 8),
             Text("Record using exact Web-Socket PCM settings (16000Hz, Mono, 16-bit) to test raw backend payload fidelity.", style: TextStyle(fontSize: 14, color: Colors.white.withValues(alpha: 0.5))),
             const SizedBox(height: 48),
             
             Center(
               child: _buildRecordButton(),
             ),
             
             if (_isRecording)
                Center(
                  child: Padding(
                    padding: const EdgeInsets.only(top: 24.0),
                    child: Text(
                      "Recording... (${_audioBuffer.length} bytes captured)",
                      style: const TextStyle(color: Colors.redAccent, fontSize: 16, fontWeight: FontWeight.w600)
                    ),
                  ),
                 ),
                 
             if (_lastWavBytes != null && !_isRecording)
               Padding(
                 padding: const EdgeInsets.only(top: 48.0),
                 child: Container(
                   padding: const EdgeInsets.all(24),
                   decoration: BoxDecoration(
                     color: Colors.white.withValues(alpha: 0.05),
                     borderRadius: BorderRadius.circular(16)
                   ),
                   child: Column(
                     crossAxisAlignment: CrossAxisAlignment.start,
                     children: [
                       Row(
                         children: [
                           Container(
                             decoration: BoxDecoration(
                               color: _isPlaying ? Colors.redAccent.withValues(alpha: 0.2) : Colors.blue.withValues(alpha: 0.2),
                               shape: BoxShape.circle,
                               border: Border.all(color: _isPlaying ? Colors.redAccent : Colors.blue, width: 2)
                             ),
                             child: IconButton(
                               icon: Icon(_isPlaying ? Icons.stop : Icons.play_arrow, color: _isPlaying ? Colors.redAccent : Colors.blue),
                               onPressed: _togglePlay,
                               iconSize: 32,
                             ),
                           ),
                           const Spacer(),
                           ElevatedButton.icon(
                             onPressed: _downloadWav,
                             icon: const Icon(Icons.download, size: 18),
                             label: const Text("Export .WAV"),
                             style: ElevatedButton.styleFrom(
                               backgroundColor: Colors.white.withValues(alpha: 0.1),
                               foregroundColor: Colors.white,
                               elevation: 0,
                               shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                             ),
                           ),
                         ],
                       ),
                       const SizedBox(height: 24),
                       const Text("Recording Analytics", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                       const SizedBox(height: 12),
                       Row(
                         children: [
                           _buildStatItem("Total Size", "${(_lastWavBytes!.length / 1024).toStringAsFixed(2)} KB"),
                           const SizedBox(width: 32),
                           _buildStatItem("Duration", "${(_audioBuffer.length / (48000 * 2)).toStringAsFixed(2)}s"),
                           const SizedBox(width: 32),
                           _buildStatItem("Format", "16-bit PCM"),
                           const SizedBox(width: 32),
                           _buildStatItem("Frequency", "48.0 kHz (Mono)"),
                         ],
                       )
                     ],
                   ),
                 ),
               )
          ],
        ),
      ),
    );
  }
  
  Widget _buildStatItem(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 0.5)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(color: Colors.white, fontSize: 14)),
      ],
    );
  }
  
  Widget _buildRecordButton() {
    return GestureDetector(
      onTap: _toggleRecord,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        width: 120,
        height: 120,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: _isRecording ? Colors.red.withValues(alpha: 0.15) : Colors.white.withValues(alpha: 0.05),
          border: Border.all(
            color: _isRecording ? Colors.redAccent : Colors.white.withValues(alpha: 0.2),
            width: _isRecording ? 4 : 2,
          ),
          boxShadow: _isRecording ? [
            BoxShadow(
              color: Colors.redAccent.withValues(alpha: 0.3),
              blurRadius: 30,
              spreadRadius: 10,
            )
          ] : [],
        ),
        child: Icon(
          _isRecording ? Icons.stop : Icons.mic,
          size: 48,
          color: _isRecording ? Colors.redAccent : Colors.white,
        ),
      ),
    );
  }
}
