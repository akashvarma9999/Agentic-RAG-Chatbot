"""
Ingestion Agent - Document Processing Module
============================================

This agent handles:
1. Reading multiple document formats (PDF, DOCX, PPTX, CSV, TXT, MD)
2. Extracting text content from documents
3. Chunking text into manageable segments
4. Embedding chunks using user-selected embedding model
5. Sending processed chunks & embeddings to Retrieval Agent via MCP
"""

import os
import PyPDF2
from docx import Document
from pptx import Presentation
import logging
from mcp import send_mcp_message
from sentence_transformers import SentenceTransformer  

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        logger.info(f"Successfully extracted text from PDF ({len(text)} characters)")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def extract_text_from_docx(file):
    try:
        doc = Document(file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        logger.info(f"Successfully extracted text from DOCX ({len(text)} characters)")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        return ""

def extract_text_from_pptx(file):
    try:
        prs = Presentation(file)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        logger.info(f"Successfully extracted text from PPTX ({len(text)} characters)")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PPTX: {str(e)}")
        return ""

def extract_text_from_txt(file):
    try:
        if isinstance(file, str):
            with open(file, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            text = file.read().decode('utf-8')
        logger.info(f"Successfully extracted text from TXT ({len(text)} characters)")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from TXT: {str(e)}")
        return ""

def extract_text_from_csv(file):
    try:
        import csv
        import io
        if isinstance(file, str):
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = file.read().decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        text = "\n".join([", ".join(row) for row in csv_reader])
        logger.info(f"Successfully extracted text from CSV ({len(text)} characters)")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from CSV: {str(e)}")
        return ""

def chunk_text(text, chunk_size=500, overlap=50):
    if not text or len(text) == 0:
        logger.warning("Empty text provided for chunking")
        return []
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        if end < text_length:
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            last_space = chunk.rfind(' ')
            break_point = max(last_period, last_newline, last_space)
            if break_point > chunk_size * 0.7:
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        chunks.append(chunk.strip())
        start = end - overlap
    logger.info(f"Text chunked into {len(chunks)} segments")
    return chunks

# ... [imports and logging as your code] ...

def load_embedding_model(embedding_model_name):
    """Dynamically load embedding model by name."""
    return SentenceTransformer(embedding_model_name)

def process_document(file, filename, embedding_model_name="all-MiniLM-L6-v2"):
    """Main processing function – embeds using user-selected model."""
    logger.info(f"Starting document processing: {filename}")

    # File type extraction
    file_extension = filename.lower().split('.')[-1]
    text = ""
    if file_extension == "pdf":
        text = extract_text_from_pdf(file)
    elif file_extension == "docx":
        text = extract_text_from_docx(file)
    elif file_extension == "pptx":
        text = extract_text_from_pptx(file)
    elif file_extension in ["txt", "md"]:
        text = extract_text_from_txt(file)
    elif file_extension == "csv":
        text = extract_text_from_csv(file)
    else:
        logger.error(f"Unsupported file type: {file_extension}")
        return False

    if not text:
        logger.error(f"No text extracted from {filename}")
        return False

    # Chunk and embed
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    if not chunks:
        logger.error(f"No chunks created from {filename}")
        return False

    embedding_model = load_embedding_model(embedding_model_name)
    logger.info(f"Loaded embedding model: {embedding_model_name}")
    embeddings = embedding_model.encode(chunks, convert_to_tensor=True)
    logger.info(f"Embedded {len(chunks)} chunks.")

    # Send to Retrieval Agent, including model name in payload
    message = {
        "sender": "IngestionAgent",
        "receiver": "RetrievalAgent",
        "payload": {
            "chunks": chunks,
            "embeddings": embeddings.cpu().tolist(),
            "document_name": filename,
            "embedding_model_name": embedding_model_name, # THIS FOR FULL TRACEABILITY!
            "metadata": {
                "file_type": file_extension,
                "chunk_count": len(chunks),
                "total_chars": len(text),
                "embedding_model_used": embedding_model_name
            }
        }
    }
    send_mcp_message(message)
    logger.info(f"Successfully processed document: {filename} with model {embedding_model_name}")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("INGESTION AGENT - Document Processing Module")
    print("=" * 60)
    print("\nSupported formats: PDF, DOCX, PPTX, CSV, TXT, MD")
    print("\nThis module extracts text and chunks documents for RAG pipeline.")
    print("\nKey Features:")
    print("  ✓ Multi-format support")
    print("  ✓ Intelligent text chunking with overlap")
    print("  ✓ Sentence-boundary aware splitting")
    print("  ✓ MCP communication for agent coordination")
    print("=" * 60)
