from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from apps.api.app.api.deps.auth import CurrentUser, get_current_user
from apps.api.app.api.deps.database import get_db
from serps_pop.identity.models import User, UserRole
from serps_pop.identity.schemas import LoginRequest, LogoutRequest, MeResponse, RefreshRequest, TokenResponse
from serps_pop.identity.services import (
    DomainConflict,
    ROLE_CANDIDATE,
    authenticate_user,
    issue_tokens,
    revoke_refresh_token,
    rotate_refresh_token,
    user_roles,
)
from serps_pop.identity_assurance.services import begin_facial_authentication

router = APIRouter()


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = authenticate_user(db, email=payload.email, password=payload.password, institution_code=payload.institution_code)
    if user is None:
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    if ROLE_CANDIDATE in user_roles(user):
        try:
            facial_stage = begin_facial_authentication(db, user)
        except DomainConflict as exc:
            db.commit()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        if facial_stage is not None:
            challenge, challenge_token = facial_stage
            db.commit()
            return {
                "authentication_stage": "facial_required",
                "challenge_id": challenge.challenge_id,
                "challenge_token": challenge_token,
                "required_actions": challenge.required_actions,
                "expires_at": challenge.expires_at,
            }
    access_token, refresh_token, _ = issue_tokens(db, user)
    db.commit()
    return {
        "authentication_stage": "complete",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 20 * 60,
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    rotated = rotate_refresh_token(db, payload.refresh_token)
    if rotated is None:
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")
    db.commit()
    access_token, refresh_token = rotated
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, expires_in=20 * 60)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: LogoutRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    revoke_refresh_token(db, payload.refresh_token, actor_user_id=current_user.user_id)
    db.commit()


@router.get("/me", response_model=MeResponse)
def me(current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> MeResponse:
    user = db.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(User.user_id == current_user.user_id)
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired credentials.")
    return MeResponse(
        user_id=user.user_id,
        institution_id=user.institution_id,
        email=user.email,
        full_name=user.full_name,
        roles=user_roles(user),
    )
