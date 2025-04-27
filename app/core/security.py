from datetime import datetime, timedelta, UTC
from typing import Optional
from jose import jwt, JWTError
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer, APIKeyHeader, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.agent_controller import AgentController

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the given data and expiration time.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_google_token(token: str) -> dict:
    """
    Verify a Google OAuth2 token and return the user information.
    
    Args:
        token: The Google OAuth2 access token
        
    Returns:
        dict: User information from Google
        
    Raises:
        HTTPException: If the token is invalid or verification fails
    """
    try:
        # Verify the token with Google's OAuth2 API
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        
        # Check if the token was issued to our client
        if idinfo['aud'] != settings.GOOGLE_CLIENT_ID:
            raise ValueError("Token was not issued for this client")
            
        # Return the user information
        return {
            "sub": idinfo["sub"],  # Google's unique user ID
            "email": idinfo["email"],
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture"),
            "email_verified": idinfo.get("email_verified", False)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )

def verify_token(token: str) -> dict:
    """
    Verify a JWT token and return the payload.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        dict: The token payload
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Create security scheme for JWT bearer token
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AgentController:
    """
    Get the current authenticated user from the JWT token.
    
    Args:
        credentials: The HTTP Authorization credentials containing the JWT token
        db: Database session
        
    Returns:
        AgentController: The current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Verify the JWT token and get the payload
        payload = verify_token(credentials.credentials)
        
        # Get user_id from token payload
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
            
        # Get user from database
        user = db.query(AgentController).filter(
            AgentController.id == user_id
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# Define the API key header scheme
api_key_header = APIKeyHeader(name="X-API-Key")

async def get_user_by_api_key(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> AgentController:
    """
    Get the current user based on their API key from the X-API-Key header.
    """
    user = db.query(AgentController).filter(
        AgentController.api_key == api_key
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
        
    return user
