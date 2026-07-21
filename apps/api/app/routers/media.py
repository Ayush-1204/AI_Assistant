import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/media", tags=["media"])

@router.get("/proxy")
async def proxy_image(url: str = Query(..., description="URL of the image to proxy")):
    """
    Proxies external images to bypass browser CORS restrictions.
    Especially useful for CanvasKit rendered Flutter Web Apps.
    """
    try:
        # We need a client instance that stays open as long as the generator runs.
        # But we must yield chunks out. Easiest way in FastAPI is to just 
        # gather headers and stream. A simpler approach is to use httpx without context block
        # passing the response generator, but it requires careful teardown.
        
        client = httpx.AsyncClient(
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        req = client.build_request("GET", url)
        r = await client.send(req, stream=True)
        if r.status_code != 200:
            await r.aclose()
            await client.aclose()
            raise HTTPException(status_code=400, detail=f"Failed to fetch image: {r.status_code}")
                
        async def image_generator():
            try:
                async for chunk in r.aiter_bytes(chunk_size=8192):
                    yield chunk
            finally:
                await r.aclose()
                await client.aclose()
                
        content_type = r.headers.get("content-type", "application/octet-stream")
        response = StreamingResponse(image_generator(), media_type=content_type)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        return response
        
    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"Request error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
