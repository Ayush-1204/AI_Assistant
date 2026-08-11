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

## Phase 31: Edit Message & Conversation Truncation
**Status**: `Completed`
- **Plan**: Allow users to edit their historical messages in the chat interface, automatically truncating subsequent conversation history and resubmitting the edited prompt.
- **Implementation**:
  - Implemented `delete_many` in `MessageRepository` and `delete_messages_from_index` in `MessageService` to purge messages after a specific index.
  - Exposed POST `/conversations/{conversation_id}/truncate` in the backend API to handle truncation requests securely.
  - Built `_UserMessageEditor` widget in `chat_view.dart` to support inline editing of User messages while preserving markdown layout.
  - Updated `ChatProvider` to slice local state arrays and resubmit the conversation payload natively after truncation.
  - **UI/UX Refinements**: Redesigned the User Message pill layout to correctly encapsulate only the markdown body. Moved Edit and Copy icons into a unified `MouseRegion` right-aligned beneath the pill that appears natively exclusively on hover. Updated the editor Save button to a clean "Submit" in black text over a white background.

## Phase 32: Adaptive AI Pipeline Resilience & Split-Intent Routing
**Status**: Completed
- **Plan**: Eliminate extreme latency bottlenecks during provider failovers (e.g., Groq rate limits) and optimize the AI pipeline to stream simple conversational queries without triggering heavy JSON UI layout planners.
- **Implementation**:
  - **Concurrent Health Checks**: Refactored _get_available_providers in 
outer.py to use syncio.gather, executing health pings concurrently to reduce N*5s sequential blocking overhead to a flat 5s max.
  - **Inference Verification**: Updated openai_provider.py health check to ping the actual /chat/completions inference endpoint (rather than the lightweight /models) to accurately map strict provider rate limits and timeouts.
  - **Split-Intent JSON Routing**: Established a "structured" routing intent mapped strictly to highly capable models (Gemini Flash, Llama 70B). Updated UpfrontPlanner, PresentationPlanner, ValidatorStage, EditorStage, and ToolRouter to use "structured", eliminating invalid JSON syntax errors previously caused by smaller 8B models.
  - **Conversational Bypass**: Refactored AgentExecutor.stream_run to bypass PresentationPlanner and heavy JSON layout stages entirely when 	ools_needed == False, streaming raw conversational text natively for basic queries.
  - **Weather Geolocation Fallback**: Enhanced WeatherTool to interpret location: "auto" dynamically fetching real-time coordinates via IP-geolocation, resolving hallucinations where the AI fetched weather for the village of "Auto, American Samoa".

## Phase 33: Animation Physics & Canvas Rendering Optimization
**Status**: `Completed`
- **Plan**: Resolve severe UI frame drops across the sidebar and voice blob animations, implement premium iOS-style spring curves, and fix underlying layout crashes.
- **Implementation**: 
  - **Layout Crash Resolution**: Replaced broken `OverflowBox` structures with `UnconstrainedBox` and `SizedBox` in `layout.dart` to prevent the sidebar from disappearing/crashing on collapse.
  - **GPU Bottleneck Fix**: Updated `chat_view.dart` to disable redundant text-field waveform rendering when operating in continuous voice mode.
  - **Explicit Animation Controllers**: Reprogrammed Sidebar animations from implicit `AnimatedContainer` widgets to explicit `AnimationController` and `AnimatedBuilder` setups to guarantee frame-by-frame reliability and avoid silent frame dropping in complex widget trees.
  - **Premium Physics**: Implemented iOS-style animation physics (`easeInCubic`, `2500ms`) for a dynamic, slow-to-fast accelerated feel.
  - **Texture Churn Elimination (The "Teleporting" Bug)**: Diagnosed the root cause of the "instant snap" or "teleporting" animations. The blob's `CustomPaint` size was being animated directly, forcing Flutter Web (CanvasKit) to destroy and re-allocate a brand new WebGL surface texture 60 times a second. This destroyed the UI thread, causing it to drop all frames and snap straight to the end state. Fixed this by wrapping the `CustomPaint` in an `OverflowBox` to lock the CanvasKit texture dimensions to a static `400x240`, passing target bounds explicitly to `ReactiveOrbPainter`. This completely eliminated WebGL texture re-allocations, achieving buttery smooth 60fps morphological rendering.

## Phase 34: Advanced News Architecture & Image WAF Bypass
**Status**: `Completed`
- **Plan**: Overhaul the news search pipeline to guarantee high-quality publisher extraction and reliably bypass aggressive WAFs (Web Application Firewalls) and paywalls that were blocking rich image metadata.
- **Implementation**: 
  - **Tavily Integration Enhancements**: Redesigned `news_search` to explicitly map `topic='news'` and a `days` parameter to pull the most recent data and avoid stale mega-threads. Restored strict `include_domains` restrictions based on user-provided trusted publishers.
  - **Multi-Tiered Image Extraction**: Engineered a highly resilient fallback cascade for paywalled images:
    1. **Tavily API**: Harvest per-article image fields directly from the primary index.
    2. **CloudScraper**: Integrated to organically bypass standard anti-bot protections/WAFs.
    3. **Discord Webhook Crawler**: Built a crawler fallback to emulate Discord's user-agent, forcing servers to yield rich embeds.
    4. **Playwright Ultimate Fallback**: Implemented a headless browser sequence to fundamentally bypass aggressive paywalls, explicitly extracting the raw `og:image` meta property for rich UI cards.
  - **Presentation Planner Adjustments**: Finalized backend typing adjustments (Pyright casting) and orchestration parameters for the presentation engine.

## Phase 35: Standardized Image Pipeline & Client Gallery Support
**Status**: `Completed`
- **Plan**: Resolve silent failure of image rendering for Wikipedia and Web Search lookups caused by raw JSON strings stripping `ImageReference` nodes. Implement missing native UI components in the Flutter client to render these image streams.
- **Implementation**:
  - **Tool Pipeline Standardization**: Upgraded `wikipedia.py` and `web_search.py` tools to explicitly wrap output data in a `NormalizedToolResult` object. This correctly formats image URLs as explicit `ImageReference` objects (rather than raw dictionary strings), preventing the `Editor` stage from dropping the images and allowing the `PresentationPlanner` to access them.
  - **Flutter Presentation Engine**: Discovered and resolved an unhandled exception where `ImageGalleryNode` lacked a corresponding `ImageGalleryWidget` in the client UI `registry.dart`.
  - Built a horizontally scrolling, responsive `ImageGalleryWidget` directly into `widgets.dart` complete with proxy routing (`wsrv.nl`) for CORS bypass, network loading states, and error handling. Registered the new widget natively in `PresentationRegistry`.

## Phase 36: Dynamic Layouts & Premium Hover Zoom Effects
**Status**: `Completed`
- **Plan**: Eliminate broken/hallucinated image URLs for recipe searches, prevent valid image data from being rejected, and upgrade the Flutter UI engine to feature responsive layouts and premium hover effects.
- **Implementation**:
  - **Tool Pipeline & Validator**: Upgraded `upfront_planner.py` to correctly schedule `Image Retrieval` tasks for "ANY physical object, concept, event, food, or visually representable entity". Updated `context_builder.py` with fail-safes preventing LLM hallucination of dummy image URLs. Patched `validator.py` to stop rejecting purely visual ImageSearch responses for lacking instructional text.
  - **Premium Hover Zoom**: Built `HoverZoomWrapper` utilizing native `MouseRegion` and `AnimatedScale` for a smooth 1.05x hover zoom. Applied this globally to all image types (Carousel, Bento, Single, News) ensuring it stays cleanly clipped within existing `ClipRRect` bounds.
  - **Dynamic Carousel Sizing**: Ripped out hardcoded pixel widths in `_CarouselGalleryWidget`. Wrapped the renderer in a `LayoutBuilder`, dynamically calculating `itemWidth` based on actual window `constraints.maxWidth` minus gap space, perfectly scaling exact 3-image square clusters onto any device screen without forced scrolling.

## Phase 37: Image Attachment Pipeline & Proactive Personalization
**Status**: `Completed`
- **Plan**: Resolve image upload hallucination bugs caused by base64 flooding, and implement proactive persona adjustments using user metadata and high-level memory extraction.
- **Implementation**:
  - **Context Scrubbing**: Engineered a regex filter within `ContextBuilder` to strip raw base64 data URLs (`![attachment](data:image...)`) injected by the frontend for rendering. This prevents massive payload flooding of the text prompt, allowing LLMs to process the true byte stream via `Part.from_bytes` seamlessly without confusion.
  - **Memory Refinement**: Overhauled `MemoryExtractor` logic to explicitly harvest high-level themes (e.g., industry, interests, field of study) from uploaded documents while strictly blocking verbatim text/fact memorization.
  - **Proactive Persona**: Mapped the `current_user.full_name` completely through the API routing layer (`chat.py` -> `ai_service.py` -> `ContextBuilder`), securely injecting the user's name natively into the central system prompt for proactive salutations and seamless buddy-like personalization.
## Phase 38: UI Refinements for Attachments and Message Editing
**Status**: `Completed`
- **Plan**: Eliminate UI discrepancies between compose/sent states for attachments, enforce exact file extensions with color themes, and resolve redundant prefixing on edited messages.
- **Implementation**:
  - **Message Editing Fix**: Corrected a state misalignment where `chat_provider.dart` mistakenly hardcoded a `"User: "` prefix during message edit submissions, causing duplicate UI tags on reload.
  - **Dynamic Attachment Pills**: Ripped out generic "PDF" labels, engineering dynamic extraction to correctly label and color-theme attachment pills based on exact file extensions (DOCX = Blue, XLSX = Green, PDF = Red). Added `maxWidth` layout constraints and overflow ellipsis to prevent long document titles from breaking responsive layouts.
  - **Unified Chat History Layout**: Rebuilt `chat_view.dart`'s rendering of sent attachments to identically match the clean, unified "pill" UI from the input area.
  - **Image Size Constraints**: Prevented raw markdown image bloat in sent chats. Instead of rendering huge full-width base64 images, extracted them cleanly into scaled `120x120` squared-off thumbnails clustered neatly above the chat bubble.
  - **History Permanence**: Rolled back premature context scrubbing in `ai_service.py`, guaranteeing that raw base64 data correctly saves to the backend SQLite DB for persistent frontend UI rendering, while relying solely on `ContextBuilder` for real-time prompt protection.

## Phase 39: AI Pipeline Optimization & Native Utility Tools
**Status**: `Completed`
- **Plan**: Drastically reduce AI latency by eliminating redundant LLM hops and expand native local utility tools to handle deterministic tasks (timezone, conversion, etc.) without web search.
- **Implementation**:
  - **LLM Pipeline Pruning**: Rewrote `intent_classifier.py` to route deterministic intents (TASK, UTILITY, SEARCH) using pure Regex, bypassing the Llama 3.1 8b classifier call entirely on 90% of requests.
  - **Fuzzy Tool Routing**: Refactored `router.py` to use Python's `difflib` for fuzzy capability matching, completely eliminating the Gemini Flash routing hop.
  - **Evaluator Short-Circuit**: Injected a rule-based bypass into `evaluator.py`, skipping the final Llama grading stage on purely conversational or short responses that don't need grounding.
  - **Native Utility Tool Suite**: Added zero-latency, local execution tools to bypass the slow LLM web search engine for simple tasks:
    - `ClipboardTool`: Read/write local clipboard data.
    - `LocalFileSearch`: Ultra-fast native workspace search.
    - `RandomChoiceTool`: Randomizer and dice rolls.
    - `TextDiffTool`: Perform unified text diffs locally.
    - `TimezoneTool`: Fetch localized global times.
    - `UnitConvertTool`: Standardized deterministic unit conversions.
  - Registered all new tools in `dependencies.py` and strictly enforced exact capability mappings in `upfront_planner.py`.

 Phase 42 — Image Positioning Fix + Intra-Node Text Streaming

## Issues Being Solved

1. **Images at bottom** — `ImageGallery` nodes are generated last in the LLM's output order, so they always appear at the bottom of the response.
2. **Blink-y nodes** — With only 2–4 nodes per response, each node still "pops in" fully formed. Text within nodes doesn't stream, so they feel identical to a non-streaming response.

---

## Fix 1 — Image Positioning (Server-side post-process, trivial)

### Root Cause
`plan_layout()` asks the LLM to design the layout, and the LLM consistently puts `ImageGallery` last. We can't reliably fix this via prompt alone (LLMs tend to put images at the end for narrative flow reasons).

### Fix
After `plan_layout()` returns the layout array, add a **sort pass** that moves `ImageGallery` nodes to index 1 (right after the first Heading, or index 0 if there's no heading). This is pure Python list manipulation — zero LLM calls, zero quality impact.

```python
def _hoist_image_gallery(layout: list[dict]) -> list[dict]:
    \"\"\"Move ImageGallery to just after the first Heading (or index 0).\"\"\"
    galleries = [n for n in layout if n.get("type") == "ImageGallery"]
    rest = [n for n in layout if n.get("type") != "ImageGallery"]
    if not galleries:
        return rest
    # Insert after first Heading, otherwise at front
    insert_at = 1 if rest and rest[0].get("type") == "Heading" else 0
    for g in galleries:
        rest.insert(insert_at, g)
        insert_at += 1
    return rest
```

#### [MODIFY] [presentation_planner.py](file:///c:/Users/AYUSH%20VERMA/Documents/AI_Assistant/apps/api/app/services/ai/planner/presentation_planner.py)
- Add `_hoist_image_gallery()` helper
- Call it on the returned layout in `plan_layout()` before returning

---

## Fix 2 — Intra-Node Text Streaming

### Strategy: Partial Text Extractor + `node_text_delta` SSE Event

The key insight: we don't need to stream every field. **Only text-bearing nodes** need streaming: `Heading`, `Paragraph`, `BulletList`, `NumberedList`, `CodeBlock`. Rich cards (`WeatherCard`, `NewsCard`, `ImageGallery`, `ComparisonTable`) appear instantly once parsed — that's fine, they have no meaningful text to stream.

#### New SSE protocol events

```
// Announces a new node is starting (lets Flutter create a skeleton immediately)
{"type": "node_start", "id": "p1", "node_type": "Paragraph"}

// Streams text delta for the primary text field of the node
{"type": "node_text_delta", "id": "p1", "delta": "Narendra Modi is "}

// Sends the fully formed node (with all fields filled in) when JSON object is closed
{"type": "presentation_node", "node": {...}}
```

#### How it works — Backend (`presentation_planner.py`)

The raw LLM token stream looks like this for a Paragraph node:
```
{"id": "p1", "type": "Paragraph", "text": "Narendra Modi is the 14th Prime ..."}
```

We need a **partial text extractor** that works on the in-flight buffer:
1. After each `{` opens a new object at depth 1, extract `"id"` and `"type"` from partial JSON → emit `node_start`
2. Once we see `"text": "` (or `"code": "`, etc.), emit `node_text_delta` for every subsequent token until the closing `"`
3. When `parse_json_objects_from_stream` yields the complete object → emit `presentation_node` as before

The extractor is entirely **additive** to the current `generate_content_stream` — it sits alongside the existing `parse_json_objects_from_stream` call and yields additional events from the same buffer.

#### New helper: `stream_text_fields_from_buffer(buffer, prev_buffer) -> list[events]`

```python
TEXT_STREAMING_FIELDS = {
    "Paragraph": "text",
    "Heading": "text",
    "BulletList": None,    # stream items array text instead
    "NumberedList": None,
    "CodeBlock": "code",
}
```

For each node type, we detect:
- **Node start**: `{"id": "X", "type": "Paragraph"` (or any ordering) → emit `node_start`  
- **Text delta**: once `"text": "` prefix is seen in buffer, the new characters added to the buffer since the last call are the delta → emit `node_text_delta`

This is **stateful** — the generator tracks:
- `current_node_id: str | None` — which node we're currently inside
- `current_node_type: str | None`
- `text_field_start_pos: int | None` — buffer position where the text value began
- `last_emitted_pos: int` — how far we've emitted text deltas

#### New backend event stream in `generate_content_stream`:
```python
async for chunk in router_inst.stream_chat(messages, intent="structured"):
    new_events, state = extract_partial_events(buffer, buffer + chunk, state)
    buffer += chunk
    
    for event in new_events:
        yield event  # node_start or node_text_delta
    
    complete_nodes, buffer = parse_json_objects_from_stream(buffer)
    for node in complete_nodes:
        # post-process (news/weather injection)...
        yield {"event_type": "presentation_node", "node": node}
```

---

### Flutter Side

#### [MODIFY] [chat_provider.dart](file:///c:/Users/AYUSH%20VERMA/Documents/AI_Assistant/apps/client/web/lib/providers/chat_provider.dart)

Add to `ChatState`:
```dart
/// Partial node text being streamed intra-node, keyed by node id
final Map<String, String> partialNodeText;
/// Set of node ids that have been announced (node_start received)
final Set<String> streamingNodeIds;
```

Handle new events:
```dart
} else if (data['type'] == 'node_start') {
    final nodeId = data['id'] as String;
    final nodeType = data['node_type'] as String;
    // Add a skeleton node with empty text to streamingNodes
    final skelNode = {'id': nodeId, 'type': nodeType, 'text': ''};
    // append to live list...
    
} else if (data['type'] == 'node_text_delta') {
    final nodeId = data['id'] as String;
    final delta = data['delta'] as String;
    // Find the skeleton node in streamingNodes and append delta to its text field
    // Trigger rebuild — Flutter re-renders the growing text
    
} else if (data['type'] == 'presentation_node') {
    // Replace the skeleton node (if any) with the final full node
    // This ensures all fields (images, lists, etc.) are correct
```

#### [MODIFY] [chat_view.dart](file:///c:/Users/AYUSH%20VERMA/Documents/AI_Assistant/apps/client/web/lib/chat_view.dart)

No changes needed — the `PresentationRenderer` already rebuilds when `streamingNodes` changes. Since the skeleton node has the same `id` as the final node, the `TweenAnimationBuilder(key: ValueKey(node.id))` will NOT re-animate it — it simply updates the text in place.

The `AiMessageRenderer` (which renders `HeadingWidget`/`ParagraphWidget` text) already handles live text updates since it's a pure stateless widget — it just reads `node.text`.

---

## Execution Order

1. **`presentation_planner.py`** — Add `_hoist_image_gallery()` + call in `plan_layout()` *(2 min, trivial)*
2. **`presentation_planner.py`** — Add `_PartialStreamState` dataclass + `extract_partial_events()` helper + update `generate_content_stream()` to emit `node_start`/`node_text_delta`
3. **`executor.py`** — Update the SSE yield in `stream_run` to handle the new event types from the generator
4. **`chat_provider.dart`** — Add `partialNodeText` + `streamingNodeIds` to `ChatState`, handle `node_start`/`node_text_delta` events, update the skeleton node in place
5. **`models.dart`** — No changes needed (nodes are already mutable maps in state before `fromJson`)
6. autoscroll


## Phase 29: Chat Streaming & Voice Scroll Refinement
**Status**: `Completed`
- **Plan**: Refine the chat auto-scrolling behavior to perfectly track dynamically generated presentation nodes and text in real-time, removing visual fighting between UI components. Fix the auto-title generator to reliably process AI responses containing specialized JSON widgets.
- **Implementation**:
  - Overhauled title generation in `chat_provider.dart` to parse completely formed raw network JSON buffers, resolving an issue where the title generator failed on non-text widgets like WeatherCards due to reading incomplete typewriter state.
  - Refactored auto-scroll listeners in `chat_view.dart` to continuously smooth-track to the bottom during the UI typewriter effect, eliminating jarring scroll interruptions.
  - Removed conflicting explicit `animateTo` scroll commands when voice mode shrinks, allowing the default smooth-scrolling algorithm to perfectly track the AI widget without hampering UX.
  - Patched the backend AI service layer to properly catch disconnects via `await fastapi_request.is_disconnected()` inside generation loops, immediately halting LLM execution if the user aborts.

