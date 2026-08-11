import re
import json

path = r"c:\Users\AYUSH VERMA\Documents\AI_Assistant\apps\client\web\lib\providers\chat_provider.dart"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace variables with maps
old_fields = """  String _networkMessageBuffer = "";
  final Map<String, String> _networkNodeTextBuffers = {};
  final Map<String, String> _networkNodeCodeBuffers = {};
  int _visibleMessageLen = 0;
  final Map<String, int> _visibleNodeTextLen = {};
  final Map<String, int> _visibleNodeCodeLen = {};
  int _currentMsgIndex = -1;
  bool _streamIsActive = false;"""

new_fields = """  final Map<int, String> _networkMessageBuffers = {};
  final Map<int, Map<String, String>> _networkNodeTextBuffers = {};
  final Map<int, Map<String, String>> _networkNodeCodeBuffers = {};
  final Map<int, int> _visibleMessageLens = {};
  final Map<int, Map<String, int>> _visibleNodeTextLens = {};
  final Map<int, Map<String, int>> _visibleNodeCodeLens = {};
  final Map<int, int> _currentMsgIndices = {};
  final Map<int, bool> _streamIsActives = {};"""

content = content.replace(old_fields, new_fields)

# Update reset buffers in sendChatMessageStream
old_reset = """      _networkMessageBuffer = "";
      _networkNodeTextBuffers.clear();
      _networkNodeCodeBuffers.clear();
      _visibleMessageLen = 0;
      _visibleNodeTextLen.clear();
      _visibleNodeCodeLen.clear();
      _currentMsgIndex = -1;
      _streamIsActive = true;"""

new_reset = """      final streamConvId = state.conversationId!;
      _networkMessageBuffers[streamConvId] = "";
      _networkNodeTextBuffers[streamConvId] = {};
      _networkNodeCodeBuffers[streamConvId] = {};
      _visibleMessageLens[streamConvId] = 0;
      _visibleNodeTextLens[streamConvId] = {};
      _visibleNodeCodeLens[streamConvId] = {};
      _currentMsgIndices[streamConvId] = -1;
      _streamIsActives[streamConvId] = true;"""

content = content.replace(old_reset, new_reset)

# In sendChatMessageStream loop
# Add background stream skip for UI updates
old_loop_start = """          try {
            final data = jsonDecode(payload);
            if (data['type'] == 'content') {"""

new_loop_start = """          final isCurrentChat = state.conversationId == streamConvId;
          try {
            final data = jsonDecode(payload);
            if (data['type'] == 'content') {"""

content = content.replace(old_loop_start, new_loop_start)

# Replace variables in the loop carefully
# The loop goes from `final stream = _apiClient.sendChatMessageStream(` to the end of the `try` block.

def replace_in_sendStream(text):
    text = text.replace('_streamIsActive = false', '_streamIsActives[streamConvId] = false')
    text = text.replace('_networkMessageBuffer', '_networkMessageBuffers[streamConvId]!')
    # For assignments we need to fix it:
    text = text.replace('_networkMessageBuffers[streamConvId]! +=', '_networkMessageBuffers[streamConvId] = (_networkMessageBuffers[streamConvId] ?? "") +')
    
    text = text.replace('_currentMsgIndex', '_currentMsgIndices[streamConvId]!')
    text = text.replace('_currentMsgIndices[streamConvId]! =', '_currentMsgIndices[streamConvId] =')
    
    text = text.replace('_networkNodeTextBuffers', '_networkNodeTextBuffers[streamConvId]!')
    text = text.replace('_networkNodeCodeBuffers', '_networkNodeCodeBuffers[streamConvId]!')
    
    # Conditional state updates based on isCurrentChat
    text = text.replace('state = state.copyWith(isProcessing: false);', 'if (isCurrentChat) state = state.copyWith(isProcessing: false);')
    text = text.replace('state = state.copyWith(messages: [...state.messages, "Assistant: "]);', 'if (isCurrentChat) state = state.copyWith(messages: [...state.messages, "Assistant: "]);')
    text = text.replace('state = state.copyWith(messageMetadata: newMeta);', 'if (isCurrentChat) state = state.copyWith(messageMetadata: newMeta);')
    text = text.replace('state = state.copyWith(streamingNodes: {...state.streamingNodes, _currentMsgIndices[streamConvId]!: currentNodes});', 'if (isCurrentChat) state = state.copyWith(streamingNodes: {...state.streamingNodes, _currentMsgIndices[streamConvId]!: currentNodes});')
    
    text = text.replace('if (state.isVoiceModeExpanded) {', 'if (isCurrentChat && state.isVoiceModeExpanded) {')
    text = text.replace('state = state.copyWith(loadingText:', 'if (isCurrentChat) state = state.copyWith(loadingText:')
    text = text.replace('state = state.copyWith(\n                isProcessing: false,\n                pendingPlan: typedPlan,\n                pendingPlanMsgIndex: _currentMsgIndices[streamConvId]!,\n              );', 'if (isCurrentChat) state = state.copyWith(\n                isProcessing: false,\n                pendingPlan: typedPlan,\n                pendingPlanMsgIndex: _currentMsgIndices[streamConvId]!,\n              );')
    
    return text

# Extract the sendChatMessageStream body to replace
start_idx = content.find('final stream = _apiClient.sendChatMessageStream(')
end_idx = content.find('if (state.isContinuousVoiceMode &&', start_idx)

if start_idx != -1 and end_idx != -1:
    body = content[start_idx:end_idx]
    new_body = replace_in_sendStream(body)
    
    # manual fix for state.copyWith multiline
    new_body = new_body.replace("""              state = state.copyWith(
                  messages: newMsgs,
                  streamingNodes: {...state.streamingNodes, _currentMsgIndices[streamConvId]!: currentNodes},
              );""", """              if (isCurrentChat) state = state.copyWith(
                  messages: newMsgs,
                  streamingNodes: {...state.streamingNodes, _currentMsgIndices[streamConvId]!: currentNodes},
              );""")
              
    content = content[:start_idx] + new_body + content[end_idx:]

# Also replace in the post-stream section:
# if (state.isContinuousVoiceMode && _networkMessageBuffer.trim().isNotEmpty)
content = content.replace('if (state.isContinuousVoiceMode && _networkMessageBuffer.trim().isNotEmpty)', 
                          'if (state.isContinuousVoiceMode && (_networkMessageBuffers[streamConvId] ?? "").trim().isNotEmpty)')
content = content.replace('readAloud(_networkMessageBuffer);', 
                          'readAloud(_networkMessageBuffers[streamConvId]!);')

content = content.replace('String cleaned = _networkMessageBuffer', 
                          'String cleaned = (_networkMessageBuffers[streamConvId] ?? "")')

# Now update _startTypewriterIfNeeded
old_typewriter = """   void _startTypewriterIfNeeded() {
      if (_typewriterTimer != null && _typewriterTimer!.isActive) return;
      _typewriterTimer = Timer.periodic(const Duration(milliseconds: 16), (timer) {
          bool didUpdate = false;
          final newMsgs = List<String>.from(state.messages);
          final currentNodes = List<Map<String, dynamic>>.from(state.streamingNodes[_currentMsgIndex] ?? []);
          
          // 1. Advance global message buffer (used for raw content, but not JSON structure)
          // (Wait, _networkMessageBuffer is also used for presentation_node json. We only want to animate if we are NOT in structured mode. If currentNodes is empty, we animate global message)
          if (currentNodes.isEmpty && _visibleMessageLen < _networkMessageBuffer.length) {
              _visibleMessageLen = (_visibleMessageLen + 3).clamp(0, _networkMessageBuffer.length);
              if (_currentMsgIndex >= 0 && _currentMsgIndex < newMsgs.length) {
                  newMsgs[_currentMsgIndex] = "Assistant: " + _networkMessageBuffer.substring(0, _visibleMessageLen);
              }
              didUpdate = true;
          }
          
          // 2. Advance node text buffers
          for (int i = 0; i < currentNodes.length; i++) {
              final node = Map<String, dynamic>.from(currentNodes[i]);
              final id = node['id'] as String;
              
              if (_networkNodeTextBuffers.containsKey(id)) {
                  final targetLen = _networkNodeTextBuffers[id]!.length;
                  final currentLen = _visibleNodeTextLen[id] ?? 0;
                  if (currentLen < targetLen) {
                      final remaining = targetLen - currentLen;
                      final step = (remaining * 0.3).ceil().clamp(1, 15);
                      _visibleNodeTextLen[id] = (currentLen + step).clamp(0, targetLen);
                      node['text'] = _networkNodeTextBuffers[id]!.substring(0, _visibleNodeTextLen[id]!);
                      currentNodes[i] = node;
                      didUpdate = true;
                  }
              }
              
              if (_networkNodeCodeBuffers.containsKey(id)) {
                  final targetLen = _networkNodeCodeBuffers[id]!.length;
                  final currentLen = _visibleNodeCodeLen[id] ?? 0;
                  if (currentLen < targetLen) {
                      _visibleNodeCodeLen[id] = (currentLen + 3).clamp(0, targetLen);
                      node['code'] = _networkNodeCodeBuffers[id]!.substring(0, _visibleNodeCodeLen[id]!);
                      currentNodes[i] = node;
                      didUpdate = true;
                  }
              }
          }
          
          if (didUpdate) {
              state = state.copyWith(
                  messages: newMsgs,
                  streamingNodes: currentNodes.isEmpty ? state.streamingNodes : {...state.streamingNodes, _currentMsgIndex: currentNodes},
              );
          } else if (!_streamIsActive) {
              timer.cancel();
          }
      });
   }"""

new_typewriter = """   void _startTypewriterIfNeeded() {
      if (_typewriterTimer != null && _typewriterTimer!.isActive) return;
      _typewriterTimer = Timer.periodic(const Duration(milliseconds: 16), (timer) {
          final convId = state.conversationId;
          if (convId == null) return;
          
          final currentMsgIndex = _currentMsgIndices[convId] ?? -1;
          final networkMessageBuffer = _networkMessageBuffers[convId] ?? "";
          var visibleMessageLen = _visibleMessageLens[convId] ?? 0;
          final streamIsActive = _streamIsActives[convId] ?? false;
          
          final networkNodeTextBuffers = _networkNodeTextBuffers[convId] ?? {};
          final networkNodeCodeBuffers = _networkNodeCodeBuffers[convId] ?? {};
          final visibleNodeTextLen = _visibleNodeTextLens[convId] ?? {};
          final visibleNodeCodeLen = _visibleNodeCodeLens[convId] ?? {};

          bool didUpdate = false;
          final newMsgs = List<String>.from(state.messages);
          final currentNodes = List<Map<String, dynamic>>.from(state.streamingNodes[currentMsgIndex] ?? []);
          
          if (currentNodes.isEmpty && visibleMessageLen < networkMessageBuffer.length) {
              visibleMessageLen = (visibleMessageLen + 3).clamp(0, networkMessageBuffer.length);
              _visibleMessageLens[convId] = visibleMessageLen;
              if (currentMsgIndex >= 0 && currentMsgIndex < newMsgs.length) {
                  newMsgs[currentMsgIndex] = "Assistant: " + networkMessageBuffer.substring(0, visibleMessageLen);
              }
              didUpdate = true;
          }
          
          for (int i = 0; i < currentNodes.length; i++) {
              final node = Map<String, dynamic>.from(currentNodes[i]);
              final id = node['id'] as String;
              
              if (networkNodeTextBuffers.containsKey(id)) {
                  final targetLen = networkNodeTextBuffers[id]!.length;
                  final currentLen = visibleNodeTextLen[id] ?? 0;
                  if (currentLen < targetLen) {
                      final remaining = targetLen - currentLen;
                      final step = (remaining * 0.3).ceil().clamp(1, 15);
                      visibleNodeTextLen[id] = (currentLen + step).clamp(0, targetLen);
                      node['text'] = networkNodeTextBuffers[id]!.substring(0, visibleNodeTextLen[id]!);
                      currentNodes[i] = node;
                      didUpdate = true;
                  }
              }
              
              if (networkNodeCodeBuffers.containsKey(id)) {
                  final targetLen = networkNodeCodeBuffers[id]!.length;
                  final currentLen = visibleNodeCodeLen[id] ?? 0;
                  if (currentLen < targetLen) {
                      visibleNodeCodeLen[id] = (currentLen + 3).clamp(0, targetLen);
                      node['code'] = networkNodeCodeBuffers[id]!.substring(0, visibleNodeCodeLen[id]!);
                      currentNodes[i] = node;
                      didUpdate = true;
                  }
              }
          }
          
          if (didUpdate) {
              state = state.copyWith(
                  messages: newMsgs,
                  streamingNodes: currentNodes.isEmpty ? state.streamingNodes : {...state.streamingNodes, currentMsgIndex: currentNodes},
              );
          } else if (!streamIsActive) {
              timer.cancel();
          }
      });
   }"""

content = content.replace(old_typewriter, new_typewriter)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied")
