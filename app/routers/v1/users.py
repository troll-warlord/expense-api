from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, DBSession
from app.schemas.common import ResponseWrapper
from app.schemas.user import UserProfileUpdate, UserRead
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def _user_service(db: DBSession) -> UserService:
    return UserService(db)


UserServiceDep = Depends(_user_service)


@router.get("/me", response_model=ResponseWrapper[UserRead], status_code=status.HTTP_200_OK)
async def get_me(current_user: CurrentUser, service: UserService = UserServiceDep):
    data = await service.get_me(current_user)
    return ResponseWrapper.ok(data=data)


@router.patch(
    "/me",
    response_model=ResponseWrapper[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Complete or update profile",
    description=("Submit first_name, last_name, and email. Sets is_profile_complete=true. Can be called again to update."),
)
async def update_profile(payload: UserProfileUpdate, current_user: CurrentUser, service: UserService = UserServiceDep):
    data = await service.update_profile(current_user, payload)
    return ResponseWrapper.ok(data=data, message="Profile updated")


@router.delete(
    "/me",
    response_model=ResponseWrapper[None],
    status_code=status.HTTP_200_OK,
    summary="Delete account",
    description="Permanently deletes the account and all associated data. Irreversible.",
)
async def delete_account(current_user: CurrentUser, service: UserService = UserServiceDep):
    await service.delete_account(current_user)
    return ResponseWrapper.ok(message="Account permanently deleted")
