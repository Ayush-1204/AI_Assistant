import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from google import genai

from app.config import get_settings

logger = logging.getLogger(__name__)

class AntigravityAgent:
    """
    Agent mapped specifically to Google's specialized managed environments leveraging the
    Interactions API and `antigravity-preview-05-2026` natively.
    """
    def __init__(self):
        self.settings = get_settings()
        # Assumes GEMINI_API_KEY is properly initialized organically via OS process injections.
        self.client = genai.Client()

    async def stream_run(
        self, 
        prompt: str,
        images: list[str] | None = None,
        previous_interaction_id: str | None = None,
        environment_id: str | None = None,
        context_messages: list[dict] | None = None
    ) -> AsyncGenerator[str, None]:
        
        # 1. Structure multimodality parameters natively
        input_data = []
        if images:
            for img in images:
                # Strip URL schemas if passed base64 directly from UI
                img_data = img
                mime_type = "image/png"
                if "," in img:
                    header, img_data = img.split(",", 1)
                    mime_type = header.split(";")[0].split(":")[1]
                input_data.append({
                    "type": "image",
                    "mime_type": mime_type,
                    "data": img_data
                })
        
        memory_context = ""
        if context_messages and len(context_messages) > 0 and context_messages[0].get("role") == "system":
            sys_content = context_messages[0].get("content", "")
            if "=== RELEVANT MEMORIES ===" in sys_content:
                memory_parts = sys_content.split("=== RELEVANT MEMORIES ===")
                if len(memory_parts) > 1:
                    memory_context = "\n\n=== RELEVANT MEMORIES ===" + memory_parts[1].split("===")[0]

        final_prompt_text = prompt + memory_context
        
        input_data.append({"type": "text", "text": final_prompt_text})
        input_payload = final_prompt_text if len(input_data) == 1 else input_data

        kwargs = {
            "agent": "antigravity-preview-05-2026",
            "input": input_payload,
            "background": True
        }
        
        # 2. Re-attach statefully if executing within continuing memory bounds
        if previous_interaction_id and environment_id:
            kwargs["previous_interaction_id"] = previous_interaction_id
            kwargs["environment"] = environment_id
        else:
            kwargs["environment"] = "remote"
            
        logger.info(f"[AntigravityAgent] Iterating deep execution sequence in ({kwargs['environment']})")
        
        # 3. Synchronous loop mapping inside Executors wrapping blocking APIs
        loop = asyncio.get_event_loop()
        try:
            import typing
            interaction = typing.cast(typing.Any, await loop.run_in_executor(None, lambda: self.client.interactions.create(**kwargs)))
            
            while interaction.status == "in_progress":
                logger.info(f"[AntigravityAgent] Long polling active run: {interaction.id}")
                yield f"data: {json.dumps({'type': 'tool', 'name': 'Sandboxing active (Executing in background...)'})}\n\n"
                
                await asyncio.sleep(6) # The API expects relaxed polling loops
                interaction = await loop.run_in_executor(
                    None, 
                    lambda id=interaction.id: self.client.interactions.get(id=id)
                )

            if interaction.status == "completed":
                yield f"data: {json.dumps({'type': 'content', 'delta': interaction.output_text})}\n\n"
                # Store the runtime IDs natively as metadata so the frontend memory holds the links natively
                metadata = {
                    "type": "interaction_state",
                    "interaction_id": interaction.id,
                    "environment_id": interaction.environment_id
                }
                yield f"data: {json.dumps(metadata)}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'content', 'delta': f'Run terminated. Final interaction status: {interaction.status}'})}\n\n"
                
        except Exception as e:
            logger.error(f"[AntigravityAgent] Pipeline crash: {str(e)}")
            yield f"data: {json.dumps({'type': 'content', 'delta': f'System Execution Error: {str(e)}'})}\n\n"

    async def run(
        self, 
        prompt: str,
        images: list[str] | None = None,
        previous_interaction_id: str | None = None,
        environment_id: str | None = None,
        context_messages: list[dict] | None = None
    ) -> str:
        
        final_text = ""
        async for chunk in self.stream_run(prompt, images, previous_interaction_id, environment_id, context_messages):
            if chunk.startswith("data: "):
                payload = chunk[6:].strip()
                if payload:
                    try:
                        data = json.loads(payload)
                        if data.get("type") == "content":
                            final_text += data.get("delta", "")
                    except:
                        pass
        return final_text
