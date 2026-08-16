import httpx
import urllib.parse
from uuid import uuid4
import logging
import hashlib

from app.services.storage_service import StorageService
from app.db.session import AsyncSessionLocal
from app.db.models.document import Document, DocumentStatus

logger = logging.getLogger(__name__)

class ImageGenerationError(Exception):
    pass

class PollinationsImageProvider:
    BASE_URL = "https://image.pollinations.ai/prompt"

    async def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        seed: int | None = None,
    ) -> bytes:
        encoded_prompt = urllib.parse.quote(prompt)
        params = {
            "width": width,
            "height": height,
            "nologo": "true",
            "model": "flux",
        }
        if seed is not None:
            params["seed"] = seed  # for reproducible variations

        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.BASE_URL}/{encoded_prompt}?{query}"

        async with httpx.AsyncClient(timeout=90) as client:
            # Generation can take 10-60s depending on load - generous timeout
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "image" not in content_type:
                raise ImageGenerationError(
                    f"Expected image, got content-type: {content_type}"
                )
            return response.content

pollinations_provider = PollinationsImageProvider()

async def handle_image_generation(prompt: str, user_id: int, storage: StorageService) -> dict:
    try:
        image_bytes = await pollinations_provider.generate(prompt)
    except (httpx.HTTPError, ImageGenerationError) as e:
        logger.warning(f"Image generation failed: {e}")
        return {
            "type": "error",
            "message": "Image generation is temporarily unavailable, try again in a moment.",
        }
        
    # Store directly via the storage service
    stored_filename, storage_path = storage.save_bytes(user_id=user_id, file_bytes=image_bytes, extension=".png")
    
    # Store in DB as well for library view
    async with AsyncSessionLocal() as db:
        sha256_hash = hashlib.sha256(image_bytes).hexdigest()
        title_snippet = prompt[:50] + "..." if len(prompt) > 50 else prompt
        doc = Document(
            user_id=user_id,
            title="Generated: " + title_snippet,
            original_filename="generated_" + stored_filename,
            stored_filename=stored_filename,
            mime_type="image/png",
            file_size=len(image_bytes),
            sha256=sha256_hash,
            storage_path=storage_path,
            status=DocumentStatus.READY
        )
        db.add(doc)
        await db.commit()
    
    # We construct a predictable local media URL (proxy via backend)
    url = f"/media/generated/{user_id}/{stored_filename}"

    # Compact reference only
    return {
        "type": "generated_image",
        "url": url,
        "prompt": prompt,
    }
