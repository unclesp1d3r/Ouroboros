from fastapi import APIRouter

from app.api.v1.endpoints.control.attacks import router as attacks_router
from app.api.v1.endpoints.control.campaigns import router as campaigns_router
from app.api.v1.endpoints.control.hash_guess import router as hash_guess_router
from app.api.v1.endpoints.control.hash_lists import router as hash_lists_router
from app.api.v1.endpoints.control.projects import router as projects_router
from app.api.v1.endpoints.control.resources import router as resources_router
from app.api.v1.endpoints.control.system import router as system_router
from app.api.v1.endpoints.control.users import router as users_router

router = APIRouter(prefix="/control", tags=["Control"])

# Note: RFC9457 error handling is implemented via custom exception classes
# that inherit from fastapi_problem.error base classes. These are automatically
# handled by the fastapi-problem library when raised in endpoints.

router.include_router(attacks_router)
router.include_router(campaigns_router)
router.include_router(hash_guess_router)
router.include_router(hash_lists_router)
router.include_router(projects_router)
router.include_router(resources_router)
router.include_router(system_router)
router.include_router(users_router)
