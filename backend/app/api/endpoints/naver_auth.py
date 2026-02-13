import os
import secrets
import axios
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User, PlatformConnection, PlatformType
from app.api.endpoints.auth import get_current_user

from app.core.config import settings

router = APIRouter()

# Use centralized settings
NAVER_CLIENT_ID = settings.NAVER_CLIENT_ID
NAVER_CLIENT_SECRET = settings.NAVER_CLIENT_SECRET
NAVER_REDIRECT_URI = settings.NAVER_REDIRECT_URI

@router.get("/auth-url")
def get_naver_auth_url(client_id: str, current_user: User = Depends(get_current_user)):
    state = secrets.token_hex(16)
    # In a real app, store 'state' in session or DB to verify in callback
    auth_url = (
        f"https://nid.naver.com/oauth2.0/authorize?"
        f"client_id={NAVER_CLIENT_ID}&"
        f"redirect_uri={NAVER_REDIRECT_URI}&"
        f"response_type=code&"
        f"state={state}&"
        f"client_id_param={client_id}" # Trick to pass client_id through
    )
    return {"auth_url": auth_url, "state": state}

@router.get("/callback")
async def naver_callback(
    code: str, 
    state: str, 
    client_id: str = None, # Pass through somehow or use state
    db: Session = Depends(get_db)
):
    # 1. Exchange code for token
    token_url = "https://nid.naver.com/oauth2.0/token"
    params = {
        "grant_type": "authorization_code",
        "client_id": NAVER_CLIENT_ID,
        "client_secret": NAVER_CLIENT_SECRET,
        "code": code,
        "state": state
    }
    
    async with axios.post(token_url, params=params) as resp:
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get token from Naver")
        token_data = resp.json()
        
    # 2. Update or Create Connection
    # Note: client_id needs to be tracked. In this simplified version, 
    # we might need to store state->client_id mapping in Redis or DB.
    
    # For now, let's assume we find a way to get client_id (e.g. from state or param)
    if not client_id:
         return {"status": "ERROR", "message": "Missing client_id"}

    # ... save to DB ...
    return {"status": "SUCCESS", "token": token_data}
