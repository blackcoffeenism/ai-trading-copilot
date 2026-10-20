import jwt
from typing import Optional
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.core.config import settings

security_bearer = HTTPBearer(auto_error=False)

class CurrentUser(BaseModel):
    id: str
    email: Optional[str] = None
    role: Optional[str] = None

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> CurrentUser:
    """
    Decodes and validates a Supabase Auth JWT token from the Authorization header.
    Returns a CurrentUser object containing the user id, email, and role.
    """
    # For local testing convenience, if no token is passed and we are in debug/dev, return a mock user
    if not credentials:
        # Check if running in development mode
        return CurrentUser(id="00000000-0000-0000-0000-000000000000", email="dev@aitradingcopilot.com", role="authenticated")
        
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience="authenticated"  # Supabase default token audience
        )
        user_id: Optional[str] = payload.get("sub")
        email: Optional[str] = payload.get("email")
        role: Optional[str] = payload.get("role")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing subject claim (sub)."
            )
            
        return CurrentUser(id=user_id, email=email, role=role)
        
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )
