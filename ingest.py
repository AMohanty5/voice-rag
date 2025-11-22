"""
Document Ingestion Script for Voice RAG Bot

This script is a standalone utility for ingesting documents from the Odisha Tourism
knowledge base into the RAG vector store. It should be run once before starting the
bot, or whenever new documents are added to the knowledge base.

Usage:
    uv run ingest.py

The script will:
1. Load environment variables (including OPENAI_API_KEY)
2. Initialize the RAG engine with ChromaDB
3. Process all .docx files in the Odisha_Tourism directory
4. Generate embeddings and store them in the vector database
5. Persist the database to disk for use by the bot

Note: This process can take several minutes depending on the number and size
of documents. The vector database is saved to ./chroma_db and will be reused
on subsequent runs unless deleted.
"""

from rag import RAGEngine
import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This includes OPENAI_API_KEY which is required for generating embeddings
load_dotenv()

def main():
    """
    Main function to ingest documents into the RAG vector store.
    
    This function:
    1. Creates a RAGEngine instance (which initializes or loads ChromaDB)
    2. Calls ingest_documents() to process all .docx files
    3. Prints a completion message
    
    The ingested data persists to ./chroma_db and will be available
    when the bot starts.
    """
    # Initialize the RAG engine
    # This will create or load the vector store from ./chroma_db
    rag = RAGEngine()
    
    # Ingest all .docx files from the Odisha_Tourism directory
    # This processes each file, splits it into chunks, generates embeddings,
    # and stores them in ChromaDB
    rag.ingest_documents("./Odisha_Tourism")
    
    # Notify user that ingestion is complete
    print("Ingestion complete.")

if __name__ == "__main__":
    main()
