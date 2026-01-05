"""
RAG (Retrieval-Augmented Generation) Tool Implementation
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import asyncio
import hashlib
import json

from .base import BaseTool, ToolExecutionResult, ToolSchema


class Document(BaseModel):
    """Document model for RAG"""
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class RAGConfig(BaseModel):
    """Configuration for RAG tool"""
    embedding_model: str = "text-embedding-ada-002"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    similarity_threshold: float = 0.7


class BaseEmbeddingModel(BaseModel):
    """Base class for embedding models"""

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text"""
        raise NotImplementedError


class BaseVectorStore(BaseModel):
    """Base class for vector storage"""

    async def add(self, documents: List[Document]):
        """Add documents to store"""
        raise NotImplementedError

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Document]:
        """Search for similar documents"""
        raise NotImplementedError


class SimpleEmbeddingModel(BaseEmbeddingModel):
    """Simple mock embedding model for testing"""

    def __init__(self, dimension: int = 1536):
        self.dimension = dimension

    async def embed(self, text: str) -> List[float]:
        """Generate simple hash-based embedding"""
        # Create a simple hash-based embedding for demonstration
        text_bytes = text.encode('utf-8')
        hash_obj = hashlib.sha256(text_bytes)

        # Use hash to generate embedding
        embedding = []
        for i in range(self.dimension):
            byte_val = hash_obj.digest()[i % 32]
            normalized = (byte_val / 255.0 - 0.5) * 2
            embedding.append(normalized)

        return embedding


class InMemoryVectorStore(BaseVectorStore):
    """In-memory vector store for testing"""

    def __init__(self):
        self.documents: List[Document] = []

    async def add(self, documents: List[Document]):
        """Add documents to store"""
        self.documents.extend(documents)

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[Document]:
        """Search using cosine similarity"""
        results = []

        for doc in self.documents:
            if doc.embedding:
                similarity = self._cosine_similarity(query_embedding, doc.embedding)
                if similarity >= threshold:
                    results.append((doc, similarity))

        # Sort by similarity and return top k
        results.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in results[:top_k]]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity"""
        import math

        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(y * y for y in b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)


class RAGTool(BaseTool):
    """
    RAG Tool for retrieval-augmented generation
    Supports document storage, retrieval, and semantic search
    """

    name = "rag_tool"
    description = "Retrieve relevant documents using semantic search"

    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        embedding_model: Optional[BaseEmbeddingModel] = None,
        vector_store: Optional[BaseVectorStore] = None
    ):
        super().__init__()
        self.config = config or RAGConfig()
        self.embedding_model = embedding_model or SimpleEmbeddingModel()
        self.vector_store = vector_store or InMemoryVectorStore()

    async def initialize(self):
        """Initialize RAG tool"""
        pass

    async def add_documents(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add documents to the RAG store"""
        documents = []

        for i, text in enumerate(texts):
            # Split text into chunks
            chunks = self._chunk_text(text)

            for j, chunk in enumerate(chunks):
                # Generate embedding
                embedding = await self.embedding_model.embed(chunk)

                # Create document
                doc = Document(
                    id=f"doc_{i}_{j}",
                    content=chunk,
                    metadata=metadata[i] if metadata and i < len(metadata) else {},
                    embedding=embedding
                )

                documents.append(doc)

        # Add to vector store
        await self.vector_store.add(documents)

        return [doc.id for doc in documents]

    async def execute(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> ToolExecutionResult:
        """Execute RAG retrieval"""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_model.embed(query)

            # Search for similar documents
            k = top_k or self.config.top_k
            results = await self.vector_store.search(
                query_embedding,
                top_k=k,
                threshold=self.config.similarity_threshold
            )

            # Format results
            context = "\n\n".join([
                f"[{doc.metadata.get('title', doc.id)}]\n{doc.content}"
                for doc in results
            ])

            return ToolExecutionResult(
                success=True,
                result={
                    "query": query,
                    "context": context,
                    "documents": [
                        {
                            "id": doc.id,
                            "content": doc.content,
                            "metadata": doc.metadata
                        }
                        for doc in results
                    ],
                    "num_results": len(results)
                }
            )

        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=str(e)
            )

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks"""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.config.chunk_size
            chunk = text[start:end]

            if len(chunk) < self.config.chunk_size:
                chunks.append(chunk)
                break

            # Try to break at word boundary
            last_space = chunk.rfind(' ')
            if last_space > 0:
                chunk = chunk[:last_space]
                start += last_space + 1
            else:
                start = end

            chunks.append(chunk.strip())

            # Add overlap
            if self.config.chunk_overlap > 0:
                start = max(0, start - self.config.chunk_overlap)

        return chunks

    def get_schema(self) -> ToolSchema:
        """Get tool schema"""
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for retrieving relevant documents"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of documents to retrieve",
                        "default": self.config.top_k
                    }
                },
                "required": ["query"]
            }
        )


class KnowledgeBase(BaseModel):
    """Knowledge base for managing RAG documents"""

    rag_tool: RAGTool
    documents: Dict[str, Document] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    async def add_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Add text document"""
        doc_ids = await self.rag_tool.add_documents(
            [text],
            [metadata or {}]
        )
        return doc_ids

    async def add_file(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Add file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            file_metadata = metadata or {}
            file_metadata["source"] = file_path

            return await self.add_text(content, file_metadata)

        except Exception as e:
            print(f"Error adding file: {e}")
            return []

    async def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Search knowledge base"""
        result = await self.rag_tool.execute(query=query, top_k=top_k)

        if result.success:
            return result.result
        else:
            return {"error": result.error}
