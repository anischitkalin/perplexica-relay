from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os
import base64

app = FastAPI(title="Perplexica Relay")

RELAY_USER = os.getenv("RELAY_USER", "perplexica")
RELAY_PASS = os.getenv("RELAY_PASS", "")
PERPLEXICA = os.getenv("PERPLEXICA_INTERNAL", "http://perplexica.railway.internal:3000")

@app.get("/health")
async def health():
    return {"status": "ok"}

def check_auth(request: Request) -> bool:
    """HTTP Basic Auth only — MCP passes credentials via user:pass@ URL."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth[6:]).decode()
        user, _, passwd = decoded.partition(":")
        return user == RELAY_USER and passwd == RELAY_PASS
    except Exception:
        return False

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy(path: str, request: Request):
    if not check_auth(request):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

    body = await request.body()
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{PERPLEXICA}/{path}"
        resp = await client.request(
            method=request.method,
            url=url,
            content=body,
            headers=headers,
        )

    return JSONResponse(content=resp.json(), status_code=resp.status_code)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))