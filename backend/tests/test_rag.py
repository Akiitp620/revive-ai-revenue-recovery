import pytest
from app.core.rag import PolicyRAG
from app.core.policy import DeterministicPolicyEngine

# A mock for OpenAIEmbeddings so we don't need real API keys during testing


class MockEmbeddings:
    def embed_documents(self, texts):
        # Return dummy embeddings (e.g. list of floats)
        return [[0.1] * 1536 for _ in texts]

    def embed_query(self, text):
        # We can implement a simple heuristic based on keywords to route to
        # different policies
        emb = [0.1] * 1536
        if "stolen" in text.lower() or "hard decline" in text.lower():
            emb[0] = 0.9  # Hard decline bias
        elif "retry" in text.lower():
            emb[1] = 0.9  # Retry bias
        return emb


@pytest.fixture
def rag_instance(monkeypatch):
    # The MockEmbeddings won't perform actual semantic search realistically
    # but we can test the indexing and integration structure.
    rag = PolicyRAG()
    # Override FAISS index with a simple custom index for testing retrieval logic if needed
    # Here we just rely on FAISS to return something, as we seeded the mock embeddings identically
    # To make it deterministic, we mock the similarity_search method of the
    # index
    return rag


def test_rag_retrieval(rag_instance, monkeypatch):
    # Mocking similarity_search to return a specific document for testing
    from langchain_core.documents import Document

    def mock_similarity_search(query, k=1):
        if "stolen" in query.lower():
            return [
                Document(
                    page_content="Hard decline policy text.",
                    metadata={
                        "policy_id": "pol_hard_decline_1",
                        "policy_version": "1.1"})]
        return [Document(
            page_content="Retry policy text.",
            metadata={"policy_id": "pol_retry_1", "policy_version": "1.0"}
        )]

    monkeypatch.setattr(
        rag_instance._index,
        "similarity_search",
        mock_similarity_search)

    results = rag_instance.retrieve_policy(
        "What policy applies to a stolen card?")

    assert len(results) == 1
    assert results[0]["policy_id"] == "pol_hard_decline_1"
    assert results[0]["policy_version"] == "1.1"


def test_rag_feeds_policy_engine():
    engine = DeterministicPolicyEngine()

    rag_context = {
        "policy_id": "pol_dynamic_123",
        "policy_version": "2.0"
    }

    event = {"amount": 100, "error_code": "stolen_card"}

    decision = engine.evaluate(
        proposed_action="RETRY_LATER",
        event=event,
        expected_net_recovery=80.0,
        merchant_allowlist=["RETRY_LATER"],
        min_recovery_threshold=5.0,
        rag_policy_context=rag_context
    )

    # Engine matches rule 1 (hard decline), but should adopt the policy_id
    # from RAG
    assert decision.final_outcome == "STOP"
    assert decision.rule_matched == "rule_1_hard_decline"
    assert decision.policy_id == "pol_dynamic_123"
    assert decision.policy_version == "2.0"

    # Verify the engine restored its original state after evaluation
    assert engine.policy_id == "pol_core_1"
