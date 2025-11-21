#!/usr/bin/env python3
"""
Quick URL shortener for Telegram Mini App
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import hashlib

app = FastAPI()

# Short URL mappings
SHORT_URLS = {
    "game": "https://65481191-1f3d-4c5e-906c-13c9cb677909-00-34h9e5dm7fk2t.worf.replit.dev/game",
    "app": "https://65481191-1f3d-4c5e-906c-13c9cb677909-00-34h9e5dm7fk2t.worf.replit.dev/game",
    "play": "https://65481191-1f3d-4c5e-906c-13c9cb677909-00-34h9e5dm7fk2t.worf.replit.dev/game"
}

@app.get("/")
async def home():
    return {"service": "URL Shortener", "available_links": list(SHORT_URLS.keys())}

@app.get("/{short_code}")
async def redirect_short_url(short_code: str):
    """Redirect short codes to full URLs"""
    if short_code in SHORT_URLS:
        return RedirectResponse(url=SHORT_URLS[short_code], status_code=301)
    else:
        raise HTTPException(status_code=404, detail="Short URL not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)