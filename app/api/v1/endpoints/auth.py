from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.core.config import settings
from app.core.security import create_access_token, verify_google_token, verify_token, get_current_user
from app.core.database import get_db
from app.schemas.agent_controller import OAuth2Request, TokenResponse
from app.models.agent_controller import AgentController

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
import uuid

router = APIRouter()

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    oauth_data: OAuth2Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Sign up a new user using Google OAuth2 token.
    """
    try:
        user_info = verify_google_token(oauth_data.access_token)
        
        stmt = select(AgentController).where(AgentController.google_id == user_info["sub"])
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        user = AgentController(
            id=str(uuid.uuid4()),
            email=user_info["email"],
            name=user_info.get("name"),
            google_id=user_info["sub"],
            api_key=str(uuid.uuid4()),
            credit_balance=10
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=datetime.now() + access_token_expires,
            agent_controller=user
        )
        
    except IntegrityError as e:
        print(f"\nINTEGRITY ERROR IN SIGNUP: {type(e).__name__}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"\nEXCEPTION CAUGHT IN SIGNUP: {type(e).__name__}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    oauth_data: OAuth2Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login using Google OAuth2 token.
    """
    try:
        user_info = verify_google_token(oauth_data.access_token)
        
        stmt = select(AgentController).where(AgentController.google_id == user_info["sub"])
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        user.last_login = datetime.now()
        await db.commit()
        await db.refresh(user)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=datetime.now() + access_token_expires,
            agent_controller=user
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/credits")
async def check_credits(
    db: AsyncSession = Depends(get_db),
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
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )

        payload = verify_token(token)
        user_id = payload.get("sub")
        
        user_id = str(user_id)
        
        stmt = select(AgentController).where(AgentController.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return {"credit_balance": user.credit_balance}
        
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
    db: AsyncSession = Depends(get_db),
    current_user: AgentController = Depends(get_current_user)
):
    """
    Delete user account and all associated data (alert prompts)
    """
    try:
        await db.delete(current_user)
        await db.commit()
        
        return {"message": "Account successfully deleted"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting account"
        )
