import logging
import os
from typing import List, Dict, Any
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

logger = logging.getLogger("robovai.chatbots.rag")

# Directory to store FAISS indices per bot
FAISS_STORAGE_PATH = "data/vectorstores"
os.makedirs(FAISS_STORAGE_PATH, exist_ok=True)

# Shared embedding model to save memory
_embeddings_model = None

def get_embeddings():
    global _embeddings_model
    if _embeddings_model is None:
        logger.info("Loading HuggingFace Embeddings model...")
        # Using a lightweight multilingual model good for Arabic
        _embeddings_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-small")
    return _embeddings_model

class RAGEngine:
    @staticmethod
    async def ingest_urls(bot_id: str, urls: List[str]) -> bool:
        """
        Scrapes a list of URLs, processes the text, and stores them in a FAISS vector database for the bot.
        """
        if not urls:
            return False
            
        try:
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
                separators=["\n\n", "\n", ".", " ", ""]
            )
            splits = text_splitter.split_documents(docs_transformed)
            
            # 4. Create/Update FAISS Vectorstore
            embeddings = get_embeddings()
            bot_db_path = os.path.join(FAISS_STORAGE_PATH, f"bot_{bot_id}")
            
            if os.path.exists(bot_db_path):
                logger.info(f"Loading existing FAISS db for bot {bot_id}")
                vectorstore = FAISS.load_local(bot_db_path, embeddings, allow_dangerous_deserialization=True)
                vectorstore.add_documents(splits)
            else:
                logger.info(f"Creating new FAISS db for bot {bot_id}")
                vectorstore = FAISS.from_documents(splits, embeddings)
                
            # 5. Save
            vectorstore.save_local(bot_db_path)
            logger.info(f"Successfully ingested {len(splits)} chunks for bot {bot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting URLs for bot {bot_id}: {e}")
            return False

    @staticmethod
    async def retrieve_context(bot_id: str, query: str, k: int = 3) -> str:
        """
        Retrieves relevant context from the bot's FAISS database based on the user query.
        """
        bot_db_path = os.path.join(FAISS_STORAGE_PATH, f"bot_{bot_id}")
        if not os.path.exists(bot_db_path):
            return ""
            
        try:
            embeddings = get_embeddings()
            vectorstore = FAISS.load_local(bot_db_path, embeddings, allow_dangerous_deserialization=True)
            
            # Perform similarity search
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
