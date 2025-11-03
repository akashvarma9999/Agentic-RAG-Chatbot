"""
Retrieval Agent - Vector Storage & Semantic Search Module
=========================================================

This agent handles:
1. Creating embeddings from text chunks using SentenceTransformer
2. Storing embeddings in FAISS vector database
3. Performing semantic search to retrieve relevant chunks
4. Managing vector store persistence


"""

import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import logging
from mcp import send_mcp_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
VECTOR_STORE_PATH = "vector_store"
EMBEDDINGS_FILE = os.path.join(VECTOR_STORE_PATH, "embeddings.pkl")
INDEX_FILE = os.path.join(VECTOR_STORE_PATH, "faiss_index.bin")

# Initialize embedding model (384-dimensional embeddings)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
logger.info("Embedding model loaded: all-MiniLM-L6-v2 (384 dimensions)")

# Global variables for vector store
vector_index = None
stored_chunks = []
document_mapping = []


def initialize_vector_store():
    """
    Initialize or load existing FAISS vector store.
    
    Creates:
    - FAISS index for similarity search
    - Storage for text chunks
    - Document metadata mapping
    """
    global vector_index, stored_chunks, document_mapping
    
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    
    # Try to load existing vector store
    if os.path.exists(INDEX_FILE) and os.path.exists(EMBEDDINGS_FILE):
        try:
            vector_index = faiss.read_index(INDEX_FILE)
            with open(EMBEDDINGS_FILE, 'rb') as f:
                data = pickle.load(f)
                stored_chunks = data['chunks']
                document_mapping = data['documents']
            logger.info(f"Loaded existing vector store: {len(stored_chunks)} chunks")
            return
        except Exception as e:
            logger.warning(f"Could not load existing vector store: {str(e)}")
    
    # Create new vector store
    dimension = 384  # Dimension of all-MiniLM-L6-v2 embeddings
    vector_index = faiss.IndexFlatL2(dimension)
    stored_chunks = []
    document_mapping = []
    logger.info("Created new FAISS vector store")


def save_vector_store():
    """
    Persist vector store to disk.
    
    Saves:
    - FAISS index (binary format)
    - Text chunks and metadata (pickle format)
    """
    try:
        faiss.write_index(vector_index, INDEX_FILE)
        with open(EMBEDDINGS_FILE, 'wb') as f:
            pickle.dump({
                'chunks': stored_chunks,
                'documents': document_mapping
            }, f)
        logger.info(f"Vector store saved: {len(stored_chunks)} chunks persisted")
    except Exception as e:
        logger.error(f"Error saving vector store: {str(e)}")


def create_embeddings(texts):
    """
    Generate embeddings for a list of text chunks.
    
    Args:
        texts (list): List of text strings to embed
        
    Returns:
        np.ndarray: Array of embeddings (shape: [n_texts, 384])
    """
    try:
        embeddings = embedding_model.encode(texts, show_progress_bar=False)
        logger.info(f"Created embeddings for {len(texts)} texts")
        return np.array(embeddings).astype('float32')
    except Exception as e:
        logger.error(f"Error creating embeddings: {str(e)}")
        return None


def store_embeddings(chunks, document_name):
    """
    Store text chunks and their embeddings in vector database.
    
    Pipeline:
    1. Generate embeddings for chunks
    2. Add embeddings to FAISS index
    3. Store text chunks with metadata
    4. Persist to disk
    
    Args:
        chunks (list): List of text chunks
        document_name (str): Name of source document
        
    Returns:
        bool: True if successful, False otherwise
    """
    global vector_index, stored_chunks, document_mapping
    
    logger.info(f"Storing embeddings for document: {document_name}")
    
    if not chunks:
        logger.warning("No chunks provided for storage")
        return False
    
    # Initialize vector store if needed
    if vector_index is None:
        initialize_vector_store()
    
    # Create embeddings
    embeddings = create_embeddings(chunks)
    if embeddings is None:
        return False
    
    # Add to FAISS index
    try:
        vector_index.add(embeddings)
        
        # Store chunks and metadata
        for chunk in chunks:
            stored_chunks.append(chunk)
            document_mapping.append(document_name)
        
        # Persist to disk
        save_vector_store()
        
        logger.info(f"Successfully stored {len(chunks)} chunks from {document_name}")
        logger.info(f"Total chunks in vector store: {len(stored_chunks)}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing embeddings: {str(e)}")
        return False


def retrieve_chunks(query, top_k=5):
    """
    Retrieve most relevant chunks for a query using semantic search.
    
    Process:
    1. Generate embedding for query
    2. Search FAISS index for similar vectors
    3. Return top-k most relevant chunks with metadata
    4. Send results to LLM Response Agent via MCP
    
    Args:
        query (str): User's question
        top_k (int): Number of chunks to retrieve (default: 5)
        
    Returns:
        list: List of tuples (chunk_text, document_name)
    """
    global vector_index, stored_chunks, document_mapping
    
    logger.info(f"Retrieving chunks for query: '{query[:50]}...'")
    
    # Initialize vector store if needed
    if vector_index is None:
        initialize_vector_store()
    
    # Check if vector store is empty
    if len(stored_chunks) == 0:
        logger.warning("Vector store is empty - no documents indexed")
        return []
    
    try:
        # Create query embedding
        query_embedding = create_embeddings([query])
        if query_embedding is None:
            return []
        
        # Search FAISS index
        distances, indices = vector_index.search(query_embedding, min(top_k, len(stored_chunks)))
        
        # Retrieve chunks and metadata
        results = []
        for idx in indices[0]:
            if idx < len(stored_chunks):  # Validity check
                chunk = stored_chunks[idx]
                doc_name = document_mapping[idx]
                results.append((chunk, doc_name))
        
        logger.info(f"Retrieved {len(results)} relevant chunks")
        
        # Log similarity scores (lower L2 distance = more similar)
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            logger.info(f"  Rank {i+1}: Distance={dist:.4f}, Doc={document_mapping[idx]}")
        
        # Send results to LLM Response Agent via MCP
        message = {
            "sender": "RetrievalAgent",
            "receiver": "LLMResponseAgent",
            "payload": {
                "query": query,
                "top_chunks": results,
                "metadata": {
                    "num_results": len(results),
                    "total_docs": len(set(document_mapping))
                }
            }
        }
        send_mcp_message(message)
        
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving chunks: {str(e)}")
        return []


def get_vector_store_stats():
    """
    Get statistics about the current vector store.
    
    Returns:
        dict: Statistics including chunk count, document count, etc.
    """
    global stored_chunks, document_mapping
    
    unique_docs = set(document_mapping)
    return {
        "total_chunks": len(stored_chunks),
        "total_documents": len(unique_docs),
        "documents": list(unique_docs),
        "index_size": vector_index.ntotal if vector_index else 0
    }


def clear_vector_store():
    """
    Clear all data from vector store (useful for testing).
    """
    global vector_index, stored_chunks, document_mapping
    
    dimension = 384
    vector_index = faiss.IndexFlatL2(dimension)
    stored_chunks = []
    document_mapping = []
    
    # Remove files
    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)
    if os.path.exists(EMBEDDINGS_FILE):
        os.remove(EMBEDDINGS_FILE)
    
    logger.info("Vector store cleared")


# Initialize on module import
initialize_vector_store()


if __name__ == "__main__":
    # Test the retrieval agent
    print("=" * 60)
    print("RETRIEVAL AGENT - Vector Storage & Semantic Search")
    print("=" * 60)
    print("\nKey Features:")
    print("  ✓ SentenceTransformer embeddings (all-MiniLM-L6-v2)")
    print("  ✓ FAISS vector database for fast similarity search")
    print("  ✓ Persistent storage with automatic save/load")
    print("  ✓ Semantic search with distance-based ranking")
    print("\nVector Store Statistics:")
    stats = get_vector_store_stats()
    print(f"  - Total chunks: {stats['total_chunks']}")
    print(f"  - Total documents: {stats['total_documents']}")
    print(f"  - Indexed vectors: {stats['index_size']}")
    if stats['documents']:
        print(f"  - Documents: {', '.join(stats['documents'])}")
    print("=" * 60)
