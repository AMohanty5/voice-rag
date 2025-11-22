"""
RAG (Retrieval-Augmented Generation) Engine Module

This module provides the core RAG functionality for the voice bot, enabling it to:
1. Ingest and process documents from the Odisha Tourism knowledge base
2. Store document embeddings in a vector database (ChromaDB)
3. Retrieve relevant context based on user queries
4. Inject retrieved context into the conversation pipeline

The RAG system enhances the bot's responses by grounding them in factual information
from the knowledge base rather than relying solely on the LLM's training data.
"""

import os
from typing import List
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from loguru import logger
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.aggregators.llm_context import LLMContext


class RAGEngine:
    """
    Core RAG engine that handles document ingestion, embedding, and retrieval.
    
    This class manages the vector database lifecycle:
    - Initializes or loads an existing ChromaDB vector store
    - Ingests .docx documents and converts them to embeddings
    - Performs similarity search to retrieve relevant context
    
    Attributes:
        persist_directory (str): Path where the vector database is stored
        embeddings (OpenAIEmbeddings): OpenAI embedding model for vectorization
        vector_store (Chroma): ChromaDB vector store instance
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize the RAG engine.
        
        Args:
            persist_directory: Directory path for storing the vector database.
                             Defaults to "./chroma_db" in the current working directory.
        """
        self.persist_directory = persist_directory
        # Initialize OpenAI embeddings using the API key from environment variables
        self.embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
        self.vector_store = None
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """
        Initialize or load the ChromaDB vector store.
        
        This method checks if a vector store already exists at the persist_directory.
        If it exists and contains data, it loads the existing store. Otherwise, it
        creates a new empty vector store.
        
        The vector store persists to disk, so ingested documents are preserved
        between application restarts.
        """
        # Check if the directory exists and is not empty
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            logger.info(f"Loading existing vector store from {self.persist_directory}")
            # Load the existing vector store with the same embedding function
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            logger.info("Initializing new vector store")
            # Create a new vector store
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )

    def ingest_documents(self, directory_path: str):
        """
        Ingest all .docx files from the specified directory into the vector store.
        
        This method:
        1. Scans the directory for .docx files
        2. Loads each document using Docx2txtLoader
        3. Splits documents into chunks for better retrieval granularity
        4. Generates embeddings and stores them in ChromaDB
        
        Args:
            directory_path: Path to the directory containing .docx files
                          (e.g., "./Odisha_Tourism")
        
        The chunking strategy uses:
        - chunk_size=1000: Maximum characters per chunk
        - chunk_overlap=200: Overlap between chunks to preserve context
        """
        logger.info(f"Ingesting documents from {directory_path}")
        documents = []
        
        # Validate that the directory exists
        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return

        # Iterate through all files in the directory
        for filename in os.listdir(directory_path):
            if filename.endswith(".docx"):
                file_path = os.path.join(directory_path, filename)
                try:
                    # Load the .docx file using langchain's Docx2txtLoader
                    loader = Docx2txtLoader(file_path)
                    docs = loader.load()
                    documents.extend(docs)
                    logger.info(f"Loaded {filename}")
                except Exception as e:
                    # Log errors but continue processing other files
                    logger.error(f"Failed to load {filename}: {e}")

        if not documents:
            logger.warning("No documents found to ingest.")
            return

        # Split documents into smaller chunks for better retrieval
        # Smaller chunks allow more precise context matching
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,        # Maximum characters per chunk
            chunk_overlap=200       # Overlap to maintain context across chunks
        )
        splits = text_splitter.split_documents(documents)
        
        if splits:
            # Add the document chunks to the vector store
            # This generates embeddings and stores them in ChromaDB
            self.vector_store.add_documents(documents=splits)
            logger.info(f"Ingested {len(splits)} chunks into vector store.")
        else:
            logger.warning("No text chunks created from documents.")

    def query(self, query_text: str, k: int = 3) -> str:
        """
        Query the vector store to retrieve relevant context.
        
        This method performs semantic similarity search to find the most relevant
        document chunks based on the query text. It uses cosine similarity between
        the query embedding and stored document embeddings.
        
        Args:
            query_text: The user's question or query text
            k: Number of most similar chunks to retrieve (default: 3)
        
        Returns:
            A string containing the concatenated content of the k most relevant chunks,
            separated by double newlines. Returns empty string if no vector store exists.
        
        Example:
            >>> engine.query("Tell me about Konark Sun Temple", k=2)
            "The Konark Sun Temple is a 13th-century temple...\\n\\nLocated in Odisha..."
        """
        if not self.vector_store:
            return ""
        
        # Perform similarity search to find the k most relevant chunks
        results = self.vector_store.similarity_search(query_text, k=k)
        
        # Concatenate the content of all retrieved chunks
        context = "\n\n".join([doc.page_content for doc in results])
        return context


class RAGProcessor(FrameProcessor):
    """
    Pipecat frame processor that integrates RAG into the conversation pipeline.
    
    This processor sits in the Pipecat pipeline between the STT (Speech-to-Text)
    and the LLM. When it receives a TextFrame containing the user's transcribed
    speech, it:
    1. Queries the RAG engine for relevant context
    2. Injects the context into the LLM conversation history
    3. Passes the frame downstream to the LLM
    
    This allows the LLM to generate responses grounded in the knowledge base.
    
    Attributes:
        rag_engine (RAGEngine): The RAG engine instance for querying
        context (LLMContext): The LLM conversation context where we inject retrieved info
    """
    
    def __init__(self, rag_engine: RAGEngine, context: LLMContext):
        """
        Initialize the RAG processor.
        
        Args:
            rag_engine: RAGEngine instance for performing similarity search
            context: LLMContext object that maintains the conversation history
        """
        super().__init__()
        self.rag_engine = rag_engine
        self.context = context

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """
        Process frames flowing through the pipeline.
        
        This method is called for every frame that passes through this processor.
        It handles:
        1. Control frames (StartFrame, etc.) by passing them to the parent class
        2. TextFrames by querying RAG and injecting context
        3. All other frames by passing them through unchanged
        
        Args:
            frame: The frame to process (could be TextFrame, AudioFrame, etc.)
            direction: The direction of the frame (DOWNSTREAM or UPSTREAM)
        
        Flow:
        - User speaks -> STT -> TextFrame -> RAGProcessor -> (context injected) -> LLM
        """
        # Call parent class to handle control frames like StartFrame
        # This is critical for proper pipeline initialization
        await super().process_frame(frame, direction)
        
        # Only process TextFrames (containing transcribed user speech)
        if isinstance(frame, TextFrame):
            text = frame.text
            # Query the RAG engine for relevant context
            context_str = self.rag_engine.query(text)
            
            if context_str:
                # Log the first 100 characters of retrieved context for debugging
                logger.info(f"RAG Context found: {context_str[:100]}...")
                
                # Inject the retrieved context as a system message
                # This appears in the conversation history before the user's message
                # The LLM will use this context to generate its response
                self.context.add_message({
                    "role": "system", 
                    "content": f"Use the following context to answer the user's question if relevant:\n\n{context_str}"
                })
        
        # Push the frame downstream to the next processor (LLM)
        await self.push_frame(frame, direction)
