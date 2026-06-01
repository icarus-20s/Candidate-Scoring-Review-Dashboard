from fastapi import APIRouter, HTTPException, Depends
from ..schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from ..services.candidate_service import create_user, get_user_by_email
from ..auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate):
    try:
        user = await create_user(
            email=data.email,
            password=data.password,
            name=data.name,
            role="reviewer",
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    token = create_access_token({
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
    })
    return TokenResponse(
        access_token=token,
        user=UserResponse(**user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await get_user_by_email(data.email)
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
    })
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
            created_at=user["created_at"],
        ),
    )


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)):
    return UserResponse(**user, created_at="")
