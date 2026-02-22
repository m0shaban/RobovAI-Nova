"""
RAG Engine for custom chatbots — lazy-loaded to avoid importing
heavy dependencies (torch / sentence-transformers) at server startup.
"""

import logging
import os
from typing import List, Dict, Any

logger = logging.getLogger("robovai.chatbots.rag")

# Directory to store Qdrant indices per bot
QDRANT_STORAGE_PATH = "data/vectorstores/qdrant"
os.makedirs(QDRANT_STORAGE_PATH, exist_ok=True)

# Shared Qdrant client to save memory
_qdrant_client = None


def get_qdrant_client():
    """Lazy-initialise a single Qdrant client."""
    global _qdrant_client
    if _qdrant_client is None:
        from qdrant_client import QdrantClient

        _qdrant_client = QdrantClient(path=QDRANT_STORAGE_PATH)
    return _qdrant_client


# Shared embedding model to save memory
_embeddings_model = None


def get_embeddings():
    """Lazy-load HuggingFace Embeddings (imports torch only here)."""
    global _embeddings_model
    if _embeddings_model is None:
        from langchain_community.embeddings import HuggingFaceEmbeddings

        logger.info("Loading HuggingFace Embeddings model...")
        _embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
    return _embeddings_model

class RAGEngine:
    @staticmethod
    async def ingest_urls(bot_id: str, urls: List[str]) -> bool:
        """Scrape URLs, chunk the text, and store in Qdrant for the bot."""
        if not urls:
            return False

        try:
            from langchain_community.document_loaders import AsyncHtmlLoader
            from langchain_community.document_transformers import Html2TextTransformer
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            from langchain_qdrant import QdrantVectorStore
            from qdrant_client.http.models import Distance, VectorParams

            logger.info(f"Scraping URLs for bot {bot_id}: {urls}")

            # 1. Load HTML
            loader = AsyncHtmlLoader(urls)
            docs = await loader.aload()

            # 2. Convert HTML to readable text
            html2text = Html2TextTransformer()
            docs_transformed = html2text.transform_documents(docs)

            # 3. Split Text
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ".", " ", ""],
            )
            splits = text_splitter.split_documents(docs_transformed)

            # 4. Create/Update Qdrant Vectorstore
            embeddings = get_embeddings()
            client = get_qdrant_client()
            collection_name = f"bot_{bot_id}"

            if not client.collection_exists(collection_name):
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )

            vectorstore = QdrantVectorStore(
                client=client,
                collection_name=collection_name,
                embedding=embeddings,
            )
            vectorstore.add_documents(splits)

            logger.info(f"Successfully ingested {len(splits)} chunks for bot {bot_id}")
            return True

        except Exception as e:
            logger.error(f"Error ingesting URLs for bot {bot_id}: {e}")
            return False

    @staticmethod
    async def retrieve_context(bot_id: str, query: str, k: int = 3) -> str:
        """Retrieve relevant context from the bot's Qdrant collection."""
        try:
            from langchain_qdrant import QdrantVectorStore

            client = get_qdrant_client()
            collection_name = f"bot_{bot_id}"

            if not client.collection_exists(collection_name):
                return ""

            embeddings = get_embeddings()
            vectorstore = QdrantVectorStore(
                client=client,
                collection_name=collection_name,
                embedding=embeddings,
            )

            docs = vectorstore.similarity_search(query, k=k)
            if not docs:
                return ""

            context = "\n\n".join([doc.page_content for doc in docs])

            # Limit context length to avoid blowing up the prompt
            if len(context) > 4000:
                context = context[:4000] + "..."

            return context
        except Exception as e:
            logger.error(f"Error retrieving context for bot {bot_id}: {e}")
            return ""

    @staticmethod
    async def ingest_pdf(bot_id: str, pdf_path: str) -> bool:
        """Extract text from a PDF and store in Qdrant for the bot."""
        try:
            from langchain_community.document_loaders import PyPDFLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            from langchain_qdrant import QdrantVectorStore
            from qdrant_client.http.models import Distance, VectorParams

            logger.info(f"Extracting PDF for bot {bot_id}: {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ".", " ", ""],
            )
            splits = text_splitter.split_documents(docs)

            embeddings = get_embeddings()
            client = get_qdrant_client()
            collection_name = f"bot_{bot_id}"

            if not client.collection_exists(collection_name):
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )

            vectorstore = QdrantVectorStore(
                client=client,
                collection_name=collection_name,
                embedding=embeddings,
            )
            vectorstore.add_documents(splits)
                
            logger.info(f"Successfully ingested {len(splits)} PDF chunks for bot {bot_id}")
            return True
        except Exception as e:
            logger.error(f"Error ingesting PDF for bot {bot_id}: {e}")
            return False
