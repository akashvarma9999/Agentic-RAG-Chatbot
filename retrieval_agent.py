import os
import faiss
import numpy as np
import pickle
import logging
from mcp import send_mcp_message
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from fuzzywuzzy import fuzz
from difflib import SequenceMatcher
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VECTOR_STORE_PATH = "vector_store"
EMBEDDINGS_FILE = os.path.join(VECTOR_STORE_PATH, "embeddings.pkl")
INDEX_FILE = os.path.join(VECTOR_STORE_PATH, "faiss_index.bin")
MODEL_DIMS = {
    "all-MiniLM-L6-v2": 384,
    "all-mpnet-base-v2": 768,
    "distilbert-base-nli-stsb-mean-tokens": 768
}

vector_index = None
stored_chunks = []
document_mapping = []
current_dim = None
current_model = None

def get_vector_dimension(model_name):
    return MODEL_DIMS.get(model_name, 384)

def load_embedding_model(model_name):
    logger.info(f"Loading embedding model: {model_name}")
    return SentenceTransformer(model_name)

def initialize_vector_store(dimension):
    global vector_index, stored_chunks, document_mapping, current_dim
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    vector_index = faiss.IndexFlatL2(dimension)
    stored_chunks = []
    document_mapping = []
    current_dim = dimension
    logger.info(f"Created new FAISS vector store (dimension: {dimension})")

def save_vector_store():
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

def clear_vector_store():
    global vector_index, stored_chunks, document_mapping, current_dim
    current_dim = None
    vector_index = None
    stored_chunks = []
    document_mapping = []
    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)
    if os.path.exists(EMBEDDINGS_FILE):
        os.remove(EMBEDDINGS_FILE)
    logger.info("Vector store cleared")

def ensure_store_for_model(embedding_model_name):
    global current_dim
    required_dim = get_vector_dimension(embedding_model_name)
    if (vector_index is None) or (current_dim != required_dim):
        clear_vector_store()
        initialize_vector_store(required_dim)

def store_embeddings(chunks, document_name, embeddings=None, embedding_model_name="all-MiniLM-L6-v2"):
    global vector_index, stored_chunks, document_mapping
    logger.info(f"Storing embeddings for document: {document_name}")

    if not chunks:
        logger.warning("No chunks provided for storage")
        return False

    ensure_store_for_model(embedding_model_name)

    emb = None
    if embeddings is not None:
        emb = np.array(embeddings).astype('float32')
        logger.info(f"Using embeddings from ingestion module ({embedding_model_name})")
    else:
        embedding_model = load_embedding_model(embedding_model_name)
        emb = embedding_model.encode(chunks, show_progress_bar=False)
        emb = np.array(emb).astype('float32')
        logger.info(f"Generated embeddings in retrieval agent ({embedding_model_name})")

    try:
        vector_index.add(emb)
        for chunk in chunks:
            stored_chunks.append(chunk)
            document_mapping.append(document_name)
        save_vector_store()
        logger.info(f"Successfully stored {len(chunks)} chunks from {document_name}")
        logger.info(f"Total chunks in vector store: {len(stored_chunks)}")

        if stored_chunks:
            logger.info(f"Sample stored chunk: {stored_chunks[0][:120]}")  # First chunk preview
            if len(stored_chunks) > 1:
                logger.info(f"Sample stored chunk 2: {stored_chunks[1][:120]}")  # Second chunk preview

        return True
    except Exception as e:
        logger.error(f"Error storing embeddings: {str(e)}")
        return False

def create_embeddings(texts, embedding_model_name="all-MiniLM-L6-v2"):
    try:
        embedding_model = load_embedding_model(embedding_model_name)
        embeddings = embedding_model.encode(texts, show_progress_bar=False)
        logger.info(f"Created embeddings for {len(texts)} texts using {embedding_model_name}")
        return np.array(embeddings).astype('float32')
    except Exception as e:
        logger.error(f"Error creating embeddings: {str(e)}")
        return None

# --- Hugging Face cross-encoder reranking utility ---
_reranker_cache = {}
def load_hf_reranker_model(model_name):
    """Load Hugging Face cross-encoder for reranking."""
    if model_name not in _reranker_cache:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        model.eval()
        _reranker_cache[model_name] = (tokenizer, model)
    return _reranker_cache[model_name]

def rerank_chunks(query, chunks, reranker_model_name=None, top_k=5):
    if not reranker_model_name or reranker_model_name == "None":
        return chunks[:top_k]

    if reranker_model_name.startswith("BAAI/bge-reranker"):
        # Use Hugging Face cross-encoder for reranking
        tokenizer, model = load_hf_reranker_model(reranker_model_name)
        texts = [chunk for chunk, _ in chunks]
        # Create query-chunk pairs as input
        pairs = [(query, text) for text in texts]

        # Tokenize (batch)
        encoded = tokenizer([q for q, t in pairs], [t for q, t in pairs],
                           padding=True, truncation=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**encoded)
            logits = outputs.logits[:, 0] if outputs.logits.shape[1] == 2 else outputs.logits.squeeze()
            scores = logits.cpu().numpy()

        # Combine score+chunk
        combined = list(zip(chunks, scores))
        combined.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in combined[:top_k]]

    else:
        # fallback: HuggingFace text-classification pipeline, not recommended for cross-encoder rerankers
        from transformers import pipeline
        reranker = pipeline("text-classification", model=reranker_model_name)
        scored = []
        for chunk, doc_name in chunks:
            pair = f"{query} [SEP] {chunk}"
            result = reranker(pair)
            score = result[0]['score'] if result else 0
            scored.append((chunk, doc_name, score))
        scored.sort(key=lambda x: x[2], reverse=True)
        return [(chunk, doc_name) for chunk, doc_name, _ in scored[:top_k]]

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def normalize(text):
    # Lowercase, remove punctuation
    return re.sub(r'[^\w\s]', '', text.lower())


def fuzz_partial_ratio(a, b):
    """Approximate fuzzywuzzy.partial_ratio using difflib."""
    a, b = a.lower(), b.lower()
    return int(SequenceMatcher(None, a, b).ratio() * 100)
# --- Keyword search utility ---
def keyword_search(query, top_k=5):
    logger.info(f"[KeywordSearch] Starting keyword search for query: {query}")

    if not query or not isinstance(query, str):
        logger.warning("[KeywordSearch] Invalid query received — must be a non-empty string.")
        return []

    if not stored_chunks:
        logger.warning("[KeywordSearch] No stored chunks available for keyword search.")
        return []

    matches = []
    query_words = query.lower().split()
    logger.info(f"[KeywordSearch] Normalized query words: {query_words}")

    for i, (chunk, doc_name) in enumerate(zip(stored_chunks, document_mapping)):
        chunk_lower = chunk.lower()

        # --- Heuristic 1: Exact word match ---
        if any(word in chunk_lower for word in query_words):
            matches.append((chunk, doc_name))
            logger.debug(f"[KeywordSearch] Exact match found in chunk #{i} (Doc: {doc_name})")

        # --- Heuristic 2: Partial substring match ---
        elif any(word[:4] in chunk_lower for word in query_words if len(word) >= 4):
            matches.append((chunk, doc_name))
            logger.debug(f"[KeywordSearch] Partial match found in chunk #{i} (Doc: {doc_name})")

        # --- Heuristic 3: Fuzzy match (optional) ---
        elif fuzz_partial_ratio(query.lower(), chunk_lower) > 75:
            matches.append((chunk, doc_name))
            logger.debug(f"[KeywordSearch] Fuzzy match found in chunk #{i} (Doc: {doc_name})")

    # --- Deduplicate and trim to top_k ---
    logger.info(f"[KeywordSearch] Matches found before dedup: {len(matches)}")
    unique_matches = list(dict.fromkeys(matches))[:top_k]

    # --- Fallback if nothing found ---
    if not unique_matches:
        logger.info("[KeywordSearch] No matches found. Returning first chunk as fallback.")
        if stored_chunks:
            return [(stored_chunks[0], document_mapping[0])]
        else:
            return []

    # --- Logging summary ---
    logger.info(f"[KeywordSearch] Returning {len(unique_matches)} unique matches")
    for i, (chunk, doc) in enumerate(unique_matches[:3]):
        logger.info(f"[KeywordSearch] Match #{i+1}: {chunk[:80]}... (Doc: {doc})")

    return unique_matches


def retrieve_chunks(query, embedding_model_name="all-MiniLM-L6-v2", reranker_model_name=None, top_k=5):
    global vector_index, stored_chunks, document_mapping
    logger.info(f"Retrieving chunks for query: '{query[:50]}...'")
    ensure_store_for_model(embedding_model_name)

    if len(stored_chunks) == 0:
        logger.warning("Vector store is empty - no documents indexed")
        return []

    try:
        query_embedding = create_embeddings([query], embedding_model_name)
        if query_embedding is None:
            return []
        distances, indices = vector_index.search(query_embedding, min(top_k, len(stored_chunks)))
        results = []
        for idx in indices[0]:
            if idx < len(stored_chunks):
                chunk = stored_chunks[idx]
                doc_name = document_mapping[idx]
                results.append((chunk, doc_name))
        logger.info(f"Retrieved {len(results)} relevant chunks")
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            logger.info(f"  Rank {i+1}: Distance={dist:.4f}, Doc={document_mapping[idx]}")

        reranked_results = rerank_chunks(query, results, reranker_model_name, top_k=top_k)

        # Send result
        message = {
            "sender": "RetrievalAgent",
            "receiver": "LLMResponseAgent",
            "payload": {
                "query": query,
                "top_chunks": reranked_results,
                "metadata": {
                    "num_results": len(reranked_results),
                    "total_docs": len(set(document_mapping)),
                    "embedding_model_used": embedding_model_name,
                    "reranker_model_used": reranker_model_name
                }
            }
        }
        send_mcp_message(message)
        return reranked_results

    except Exception as e:
        logger.error(f"Error retrieving chunks: {str(e)}")
        return []

def get_vector_store_stats():
    global stored_chunks, document_mapping
    unique_docs = set(document_mapping)
    return {
        "total_chunks": len(stored_chunks),
        "total_documents": len(unique_docs),
        "documents": list(unique_docs),
        "index_size": vector_index.ntotal if vector_index else 0
    }

if __name__ == "__main__":
    print("=" * 60)
    print("RETRIEVAL AGENT - Vector Storage & Semantic Search")
    print("=" * 60)
    print("\nKey Features:")
    print("  ✓ SentenceTransformer embeddings (multi-model, dynamic)")
    print("  ✓ FAISS vector database for fast similarity search")
    print("  ✓ HuggingFace post-retrieval reranking (BGE, etc)")
    print("  ✓ Keyword search for document chunks")
    print("  ✓ Persistent storage with automatic save/load")
    print("  ✓ Semantic and reranked search with distance-based ranking")
    print("\nVector Store Statistics:")
    stats = get_vector_store_stats()
    print(f"  - Total chunks: {stats['total_chunks']}")
    print(f"  - Total documents: {stats['total_documents']}")
    print(f"  - Indexed vectors: {stats['index_size']}")
    if stats['documents']:
        print(f"  - Documents: {', '.join(stats['documents'])}")
    print("=" * 60)
