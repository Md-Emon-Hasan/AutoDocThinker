"""Consolidated tests for all Pydantic schemas."""

from app.schemas.chat import MessageRequest, SelectProfileRequest, SessionOut
from app.schemas.common import MessageOut
from app.schemas.domain import DomainOut
from app.schemas.error import ErrorOut
from app.schemas.health import HealthOut
from app.schemas.history import HistoryMessage
from app.schemas.index import IndexStatusOut
from app.schemas.ingestion import IngestRequest, IngestResponse, IngestTextRequest
from app.schemas.rag import QueryRequest, QueryResponse
from app.schemas.rag_profile import RAGProfileOut
from app.schemas.source import SourceOut


class TestSchemas:
    def test_session_out(self):
        s = SessionOut(session_id="x", domain="g", rag_mode="n", history=[])
        assert s.session_id == "x"

    def test_select_profile(self):
        assert SelectProfileRequest(domain="legal", rag_mode="crag").domain == "legal"

    def test_message_request(self):
        r = MessageRequest(message="hi")
        assert r.message == "hi" and r.metadata_filter is None

    def test_health(self):
        assert HealthOut(status="ok").status == "ok"

    def test_index_status(self):
        assert IndexStatusOut(total_chunks=1, sources=["s"]).total_chunks == 1

    def test_source(self):
        assert SourceOut(id=1, label="s").id == 1

    def test_history(self):
        assert HistoryMessage(role="user", content="hi").role == "user"

    def test_error(self):
        assert ErrorOut(detail="bad").detail == "bad"

    def test_message_out(self):
        assert MessageOut(message="ok").message == "ok"

    def test_rag_profile(self):
        assert RAGProfileOut(domain="g", rag_modes=["n"]).rag_modes == ["n"]

    def test_domain_out(self):
        assert DomainOut(name="x", label="X", description="d").name == "x"

    def test_ingest_request(self):
        assert IngestRequest(source="p", file_type="txt").source == "p"

    def test_ingest_text_default_title(self):
        assert IngestTextRequest(text="hi").title == "pasted_text"

    def test_ingest_response(self):
        assert (
            IngestResponse(chunks_added=5, total_chunks=10, sources=["a"]).chunks_added
            == 5
        )

    def test_query_request_defaults(self):
        r = QueryRequest(question="q")
        assert r.domain == "general" and r.rag_mode == "advanced"

    def test_query_response(self):
        r = QueryResponse(
            answer="a", sources=[], history=[], mode="n", domain="g", metadata={}
        )
        assert r.answer == "a"
