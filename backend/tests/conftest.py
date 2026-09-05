import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from app.core.agent import AgentRecommendation

# Dummy classes for mocking Gemini in tests

class MockEmbeddings:
    def __init__(self, *args, **kwargs):
        pass

    def embed_documents(self, texts):
        return [[0.1] * 1536 for _ in texts]

    def embed_query(self, text):
        emb = [0.1] * 1536
        if "stolen" in text.lower() or "hard decline" in text.lower():
            emb[0] = 0.9
        elif "retry" in text.lower():
            emb[1] = 0.9
        return emb

class FakeStructuredLLM:
    def __init__(self, response_obj):
        self.response_obj = response_obj

    def invoke(self, prompt: str):
        return self.response_obj

class FakeChatModelWrapper:
    def __init__(self, *args, **kwargs):
        # Determine what to return. If response_obj is passed in tests, use it.
        # Otherwise default to a RETRY_LATER action for api tests.
        self.response_obj = kwargs.get("response_obj") or AgentRecommendation(
            strategy="RETRY_LATER",
            confidence=0.85,
            supporting_evidence=[],
            missing_evidence=[]
        )

    def with_structured_output(self, schema):
        return FakeStructuredLLM(self.response_obj)
        
    def invoke(self, prompt: str):
        return self.response_obj

@pytest.fixture(autouse=True)
def mock_gemini_services(monkeypatch):
    """
    Automatically mock Google Gemini services for all tests to ensure they are
    deterministic and independent of external API credentials.
    """
    # Prevent accidental network calls by setting a dummy key, though we mock the classes anyway
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy_key_for_tests")
    
    # Patch in rag.py
    monkeypatch.setattr("app.core.rag.GoogleGenerativeAIEmbeddings", MockEmbeddings)
    
    # Patch in api_service.py by patching the module it imports from
    import langchain_google_genai
    monkeypatch.setattr("langchain_google_genai.ChatGoogleGenerativeAI", FakeChatModelWrapper)
