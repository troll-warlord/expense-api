from fastapi import APIRouter

from app.routers.v1 import auth, categories, payment_methods, transactions, users

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(auth.router)
v1_router.include_router(users.router)
v1_router.include_router(categories.router)
v1_router.include_router(payment_methods.router)
v1_router.include_router(transactions.router)
