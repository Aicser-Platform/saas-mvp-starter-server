from fastapi import APIRouter
from app.api.v1.endpoints import (
    users, 
    courses, 
    payments, 
    plans, 
    subscriptions, 
    billing_accounts, 
    lessons, 
    course_progress, 
    lesson_progress,
    files,
    stripe,
)

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(courses.router)
api_router.include_router(payments.router)
api_router.include_router(plans.router)
api_router.include_router(subscriptions.router)
api_router.include_router(billing_accounts.router)
api_router.include_router(lessons.router)
api_router.include_router(course_progress.router)
api_router.include_router(lesson_progress.router)
api_router.include_router(files.router)
api_router.include_router(stripe.router)
