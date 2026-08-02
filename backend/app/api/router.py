from fastapi import APIRouter

from app.api.admin_routes import router as admin_router
from app.api.chat_routes import router as chat_router
from app.api.domain_routes import router as domain_router
from app.api.governance_routes import router as governance_router
from app.api.health_routes import router as health_router
from app.api.hitl_routes import router as hitl_router
from app.api.index_routes import router as index_router
from app.api.ingestion_routes import router as ingestion_router
from app.api.memory_routes import router as memory_router
from app.api.rag_routes import router as rag_router
from app.api.stream_routes import router as stream_router

router = APIRouter()
router.include_router(health_router)
router.include_router(domain_router)
router.include_router(rag_router)
router.include_router(chat_router)
router.include_router(ingestion_router)
router.include_router(index_router)
router.include_router(admin_router)
router.include_router(governance_router)
router.include_router(hitl_router)
router.include_router(memory_router)
router.include_router(stream_router)
