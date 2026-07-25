# Development Log: Phase 9 to Phase 28

This document aggregates the implementation plans and walkthrough summaries for Phases 9 through 28, detailing the architectural decisions, structural refactoring, and UI/UX improvements deployed to the Personal AI Assistant.

---

## Phase 9: High-Speed OSS Model Orchestration
**Status**: `Completed`
- **Plan**: Inject a list of advanced high-compatibility open-source models (Qwen, Llama 3, Compound, Orpheus-VL, GPT-OSS). Dynamically load them via standard `OpenAICompatibleProvider` shims over the Groq/OpenRouter configurations, prioritizing ultra-fast inference first.
- **Implementation**: Successfully instantiated native parsing arrays for Groq (`llama-3.3-70b-versatile`, `qwen3.6-27b`, `groq/compound`, etc) and OpenRouter (`openai/gpt-oss-120b`, `canopylabs/orpheus-vl-english`). Reshaped `IntentBasedRoutingStrategy` to immediately prioritize fast edge models for quick conversational loops, code requests, and UI abstractions.

## Phase 10: Multi-Tiered TTS Orchestrator
**Status**: `Completed`
- **Plan**: Integrate premium text-to-speech providers to radically improve latency and prosody. Deploy a cascading fallback system spanning Deepgram, ElevenLabs, and Edge TTS.
- **Implementation**: Configured highly specialized abstract wrapper classes mimicking the AI's BaseTTS interface (`DeepgramTTSProvider` and `ElevenLabsTTSProvider`). Overhauled the central `/voice/tts` API, generating full-payload bytes specifically for Flutter Web, structurally wrapped with a rigid try-except sequence: `Deepgram -> ElevenLabs -> EdgeTTS`. Re-mapped the native Voice WebSocket to intelligently instantiate the precise `BaseTTSProvider` derivative based on available configuration keys.

## Phase 11: Frontend Audio Sandbox
**Status**: `Completed`
- **Plan**: Build a standalone diagnostics page within the Flutter web application to mirror the exact `pcm16bits` dictation recording sequence and play back the physical bytestream locally.
- **Implementation**: 
  - Implemented `audio_debug_view.dart` encapsulating a native RIFF-WAVE header generator directly in Dart. 
  - Registered `AudioDebugView` natively inside the application's root Sidebar (`Audio Sandbox`). 
  - Wired up `dart:html` Blobs linked directly to dynamic Anchor URLs for instant, zero-backend native downloading of byte-perfect recording frames. 
  - Overhauled `chat_provider.dart` to poll raw microphone amplitude decibel mappings at ultra-low latency frequencies (50ms). Injected these streams into `ChatState` to normalize background floors and manipulate `ActiveVoiceBar` natively.

## Phase 12: Chat UI & UX Overhaul
**Status**: `Completed`
- **Plan**: Restrict chat message `ListView` to `800px` max-width. Wire native Keyboard Handlers to trap `Enter` and `Shift+Enter`. Add richer Markdown Elements. Clean up "Empty State".
- **Implementation**: 
  - Overhauled renderer constraining both history stream and compose bar into an absolute `800px` max-width container locked to the viewport center. 
  - Reprogrammed hardware `Focus` input listeners wrapping the main textfield for native keyboard payload drops. 
  - Rewrote the raw `MarkdownStyleSheet` injection points binding uniform syntax styling. 
  - Scrubbed hardcoded UI greetings and integrated a pristine new centralized landing screen complete with a hovering compose bar.

## Phase 13: DNS & Network Resilience Patch
**Status**: `Completed`
- **Plan**: Expand backend capabilities to bypass `getaddrinfo failed` network exceptions across async TCP/DNS loops.
- **Implementation**: Diagnosed OS-level DNS socket dropping mapping `ssl_connect` inside Python's async event loop. Implemented `httpx.Limits(max_keepalive_connections=50, max_connections=100)` inside `OpenAICompatibleProvider` to rigorously throttle unbound TCP socket generation on multi-LLM endpoints. Expanded `dashboard.py` to intercept structural network layer destruction and organically yield a "Sensors Offline" payload.

## Phase 14: Advanced Interactive Voice Mode
**Status**: `Completed`
- **Plan**: Build a standalone `voice_view.dart` interface powered by a continuous, organic "liquid gradient blob" reminiscent of ChatGPT's Voice UX.
- **Implementation**: Engineered a dedicated Voice Sandbox screen structurally detached from standard text-chat routing. Implemented `BlobPainter` and `BlobOrb` utilizing sum-of-sines noise variants to yield a continuous, liquid-gradient "Aura Orb" interface. Hardcoded continuous Voice Flow sequential execution rules into `chat_provider.dart` dynamically toggling audio player streams against Voice Mode limits.

## Phase 15: Voice Physics & Morphology
**Status**: `Completed`
- **Plan**: Separate the Voice blob visually into distinct physics states (idle, listening, and speaking) by incorporating damped spring physics and an active cross-fade flatten modifier into a layered waveform.
- **Implementation**: Restructured `voice_view.dart` into `ReactiveOrbPainter` and `ReactiveVoiceOrb` relying on raw Ticker interactions native to Flutter `Scheduler`. Separated interactions into strict boundaries (Idle, Listening, Speaking). Fully wired the backend payload streams inside `ChatProvider` mapping raw `Uint8List` buffer packets into the `calculateRms` engine to render native PCM waveform metrics into screen physics.

## Phase 16: API Optimization & Token Rate Limiting
**Status**: `Completed`
- **Implementation**: Eradicated extreme API polling loop causing heavy token limit spikes entirely localized to `fetchDashboardWidgets()` by caching the UI resolution inside `_ChatViewState.initState()`.

## Phase 17: Apple Intelligence Fluid Typography
**Status**: `Completed`
- **Implementation**: Overhauled visual components within `voice_view.dart` to rely on parametric Lissajous curves (utilizing sine and cosine wave cross-mapping instead of baseline horizontal bands). Mimics a volumetric Sweep Gradient emitting twisting figure-8 ribbons dynamically reacting to `dt` physical spring simulations while natively drawing an additive fusion core across overlapping paths.

## Phase 18: Continuous Live TTS Reply Loop
**Status**: `Completed`
- **Plan**: Continuously loop transcription and STT when operating in the continuous voice sandbox mapping.
- **Implementation**: Hooked `readAloud(assistantReply)` directly onto the completion phase of `sendMessage()` isolated heavily around the `isContinuousVoiceMode` toggle. Built a natively persistent conversation loop inside `ChatProvider` where the Voice interface speaks aloud automatically, inherently tripping the `.onPlayerComplete` stream logic to instantly open the Mic to listen for the next input without human touch.

## Phase 19: Voice Mode Transcript UI Integration 
**Status**: `Completed`
- **Plan**: Render active historical textual data dynamically bounded across the active Voice Orb background.
- **Implementation**: Replaced the singular generic `liveTranscript` label inside Voice Mode with a fully native `ListView(reverse: true)` mapping the actual active conversation history (`state.messages`). Injected a `ShaderMask` combining `BlendMode.dstIn` and a vertical `LinearGradient` across the ListView allowing historic text to smoothly fade into transparency at the upper bounds exactly like iOS Siri.

## Phase 20: Dictation Artifact Filtration and STT Accuracy
**Status**: `Completed`
- **Implementation**: Stripped the obsolete `_drawDashedRing` function inherently attached to the Voice Painter context. Injected conditional operators around transcription payloads triggering message cascades to discard identical matches on Voice-Activity hallucinations specifically targeting single period and ellipsis (`.` and `...`) structures. Updated the recording payload hardware constraint explicitly bridging 16kHz to natively match Whisper bounds for reduced latency.

## Phase 21: Voice Mode Deep Integration
**Status**: `Completed`
- **Plan**: Replace text box icons triggering transitions natively with localized page builders replacing standard popups with fluid boundaries locked to layout width standards.
- **Implementation**: Eradicated `Voice Mode` from the overarching layout sidebar mapping to convert the sandbox into a localized chat flow. Built a natively drawn custom `WaveformCircleIcon` mimicking Apple-Intelligence. Replaced Chat Interface 'Listening' toggle with the new Voice action attaching a 500ms curved `PageRouteBuilder` to achieve a fluent Aura expansion mechanic into Voice Mode. Refactored tracking logic to recognize `System:` tags injecting explicit 1-pixel horizontal Timeline Dividers natively marking entry boundaries.

## Phase 22: UI Polish and Dynamic Send/Voice Button
**Status**: `Completed`
- **Plan**: Overhaul trailing modifiers resolving Send vs Action boundaries, strip timeline markers from Voice histories automatically, format `User:` tags smoothly.
- **Implementation**: 
  - Bound the Voice Mode `WaveformCircleIcon` dynamically onto an identical `IconButton` action cluster via a `ValueListenableBuilder` (yields mimicking ChatGPT native behaviors: Empty fields show Voice Aura; explicit strings swap to standard Send Array).
  - Pared the Custom Voice Icon explicitly down to 4 visual payload bars matching strict design limits exactly.
  - Re-routed historic conversation parsing schemas masking arbitrary `System:` payload data out of the Voice UI completely, along with stripping active persistent `User: ` prefixes off chat bubbles natively.
  - Dropped excessive `Sessions/Recent` popup array layouts directly from the overarching top action bar per user UX refinements.

## Phase 23: Native Function Calling Strategy & Provider Tool Mapping
**Status**: `Completed`
- **Plan**: Restore native function calling across all LLM providers (Gemini, Groq, OpenRouter) and fix tool translation schemas.
- **Implementation**:
  - Re-enabled `supports_native_tools = True` in `router.py` to bypass unstable XML fallback strategies.
  - Updated `openai_provider.py` to map Gemini `function_declarations` schemas into OpenAI-compatible `tools` schemas seamlessly.
  - Ensured native function call extraction and execution work uniformly across all providers.

## Phase 24: Scheduled Task UI Separators & Automation Pipeline
**Status**: `Completed`
- **Plan**: Align automated scheduled job outputs with normal user chat flows while standardizing UI representation.
- **Implementation**:
  - Updated `dispatcher.py` to append Date/Title metadata to automated job triggers while preserving raw user directives intact.
  - Built a frontend interceptor in `chat_view.dart` to hide raw `[AUTOMATED SCHEDULED TRIGGER]` text, rendering a pristine system separator pill displaying the task Title and Date.

## Phase 25: Open-Meteo Weather Service API Tool
**Status**: `Completed`
- **Plan**: Provide dedicated weather lookup capabilities directly to both live chat and background tasks to prevent LLM web search hallucinations.
- **Implementation**:
  - Implemented `WeatherTool` in `app/services/ai/tools/weather.py` utilizing the Open-Meteo Geocoding and Forecast APIs via `httpx`.
  - Registered `WeatherTool` in `ToolOrchestrator` (`dependencies.py`), providing exact current conditions, humidity, wind, and 5-day forecasts.

## Phase 26: OpenAI Streaming Tool-Call Delta Buffering & Forced Tool Choice
**Status**: `Completed`
- **Plan**: Resolve tool execution failures during SSE streaming requests on OpenAI/Groq endpoints and enforce tool calls when intent requires search.
- **Implementation**:
  - Added a `tool_calls_buffer` inside `stream_chat` in `openai_provider.py` to accumulate streamed function arguments and yield a `MockResponse` upon stream completion.
  - Added dynamic `tool_choice: "required"` injection when `intent == "SEARCH"` for initial execution steps (safeguarded against loop recursion).
  - Enhanced `PromptBuilder.chat()` to safely serialize native `parts` array structures in message history, resolving `KeyError: 'content'` during provider failover.

## Phase 27: E2B Cloud Sandbox Code Interpreter Integration
**Status**: `Completed`
- **Plan**: Fix desktop computer control dependencies and implement a secure Python code interpreter sandbox for complex computation and data analysis.
- **Implementation**:
  - Installed `pyautogui`, `Pillow`, and `e2b_code_interpreter` in the backend virtual environment, restoring full functionality to `ComputerControlTool`.
  - Implemented `CodeInterpreterTool` in `app/services/ai/tools/code_interpreter.py` using `Sandbox.create()` from `e2b_code_interpreter`.
  - Added `E2B_API_KEY` to `config.py` and registered `CodeInterpreterTool` in `dependencies.py` to run untrusted code in Firecracker microVM sandboxes.

## Phase 28: Native Knowledge & Research Tools Suite
**Status**: `Completed`
- **Plan**: Expand the AI's research capabilities with specialized factual, scientific, and mathematical lookup APIs.
- **Implementation**:
  - Built 4 zero-dependency tools using raw `httpx` and built-in Python parsers:
    - `WikipediaTool`: Fast, factual entity lookups via Wikipedia REST API.
    - `WolframAlphaTool`: Quantitative and scientific reasoning via Wolfram Alpha Spoken Results API (added `WOLFRAM_ALPHA_APP_ID` to `config.py`).
    - `ArxivTool`: Academic paper search and abstract retrieval via arXiv Atom feed API.
    - `SemanticScholarTool`: Citation graphs and literature search via Semantic Scholar API.
  - Registered all 4 tools in `dependencies.py` and updated the `ai_tools_list.md` artifact.

## Phase 29: Image Verification, Local Proxy, and ImageSearchTool
**Status**: `Completed`
- **Plan**: Eliminate broken/hallucinated image URLs in LLM responses and bypass CORS/hotlinking restrictions (e.g. Wikimedia blocks).
- **Implementation**:
  - Created `ImageSearchTool` in `app/services/ai/tools/image_search.py` using Wikipedia API to search images, performing HTTP `HEAD` verification requests to ensure the image exists (`200 OK`) and has `Content-Type: image/*`.
  - Routed verified image URLs through the local backend proxy endpoint `/media/proxy?url=...` (in `app/routers/media.py`) to bypass CORS and hotlinking blocks on Flutter Web.
  - Updated system prompt in `context_builder.py` to strictly forbid hallucinated/unverified image URLs and Wikimedia hotlinks.
  - Registered `ImageSearchTool` in `dependencies.py`.

## Phase 30: Tool Hardening & Resilience Patches
**Status**: `Completed`
- **Plan**: Resolve 308 redirects, output capture bugs, rate-limit failures, and keypress handling across tools.
- **Implementation**:
  - Fixed `WolframAlphaTool` to use `https://api.wolframalpha.com` instead of `http://`, resolving 308 Permanent Redirect errors.
  - Updated `CodeInterpreterTool` to capture standard output from `execution.logs.stdout` and `execution.logs.stderr` (matching the updated `e2b_code_interpreter` V1 SDK) instead of legacy `execution.text`.
  - Added an `asyncio.sleep` retry loop to `SemanticScholarTool` for handling HTTP 429 rate limit responses.
  - Enhanced `ComputerControlTool` to handle key combinations (e.g., `win+down`) by splitting on `+` and calling `pyautogui.hotkey()`.

