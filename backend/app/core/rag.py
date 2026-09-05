import json
from pathlib import Path
from typing import Dict, Any, List

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS


class PolicyRAG:
    """
    Minimal policy RAG layer using FAISS.
    """

    def __init__(self, corpus_path: str = "app/core/policy_corpus.json"):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
        self.corpus_path = corpus_path
        self._index = self._build_index()

    def _build_index(self) -> FAISS:
        """Load corpus and build in-memory FAISS index."""
        corpus_file = Path(__file__).parent / "policy_corpus.json"

        with open(corpus_file, "r") as f:
            corpus = json.load(f)

        documents = []
        for policy in corpus:
            doc = Document(
                page_content=policy["text"],
                metadata={
                    "policy_id": policy["id"],
                    "policy_version": policy["version"],
                    "section": policy["section"],
                    **policy.get("metadata", {})
                }
            )
            documents.append(doc)

        # Build FAISS index
        return FAISS.from_documents(documents, self.embeddings)

    def retrieve_policy(self, query: str, k: int = 1) -> List[Dict[str, Any]]:
        """
        Retrieves the most relevant policy given a query.
        Returns:
            list of dicts containing: policy_id, policy_version, text, metadata
        """
        docs = self._index.similarity_search(query, k=k)

        results = []
        for doc in docs:
            results.append({
                "policy_id": doc.metadata.get("policy_id", "unknown"),
                "policy_version": doc.metadata.get("policy_version", "unknown"),
                "text": doc.page_content,
                "metadata": doc.metadata
            })

        return results
