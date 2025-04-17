from datetime import datetime, timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.core.security import create_access_token, verify_google_token, verify_token
from app.core.database import get_db
from app.schemas.agent_controller import OAuth2Request, TokenResponse
from app.models.agent_controller import AgentController
from jose import JWTError

router = APIRouter()

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    oauth_data: OAuth2Request,
    db: Session = Depends(get_db)
):
    """
    Sign up a new user using Google OAuth2 token.
    """
    try:
        # Verify Google token and get user info
        user_info = verify_google_token(oauth_data.access_token)
        
        # Check if user already exists
        existing_user = db.query(AgentController).filter(
            AgentController.google_id == user_info["sub"]
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        # Create new user
        user = AgentController(
            id=uuid.uuid4(),
            email=user_info["email"],
            name=user_info.get("name"),
            google_id=user_info["sub"],
            api_key=str(uuid.uuid4()),  # Generate a unique API key
            credits=0
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=datetime.utcnow() + access_token_expires,
            agent_controller=user
        )
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    oauth_data: OAuth2Request,
    db: Session = Depends(get_db)
):
    """
    Login using Google OAuth2 token.
    """
    try:
        # Verify Google token and get user info
        user_info = verify_google_token(oauth_data.access_token)
        
        # Check if user exists
        user = db.query(AgentController).filter(
            AgentController.google_id == user_info["sub"]
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=datetime.utcnow() + access_token_expires,
            agent_controller=user
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )

@router.get("/credits")
async def check_credits(
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    """
    Get the current user's credit balance.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
        
    try:
        # Extract token from Authorization header
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
            
        # Verify token and get user ID
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        # Get user from database
        user = db.query(AgentController).filter(
            AgentController.id == user_id
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return {"credits": user.credits}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.delete("/account", status_code=status.HTTP_200_OK)
async def delete_account(
    db: Session = Depends(get_db),
    current_user: AgentController = Depends(get_current_user)
):
    """
    Delete user account and all associated data (alert prompts)
    """
    try:
        # Get user with their relationships
        user = db.query(AgentController).filter(
            AgentController.id == current_user.id
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        # Delete user (this will cascade delete alert_prompts due to relationship)
        db.delete(user)
        db.commit()
        
        return {"message": "Account successfully deleted"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting account"
        )

#let user delete account