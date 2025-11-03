"""
LLM Response Agent - Answer Generation Module
=============================================

This agent handles:
1. Receiving query and retrieved chunks from Retrieval Agent
2. Constructing context-aware prompts
3. Generating responses using Groq LLM (multiple models supported)
4. Tracking sources and model usage
5. Error handling and fallback responses


"""

from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables - FIX: Specify exact path to .env
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    logger.error(f"GROQ_API_KEY not found in environment variables!")
    logger.error(f"Checked .env file at: {env_path.absolute()}")
    logger.error(f".env file exists: {env_path.exists()}")
    if env_path.exists():
        logger.error("Please check that .env contains: GROQ_API_KEY=gsk_your_key")
    else:
        logger.error("Please create .env file in the same folder as this script")
    raise ValueError("Please set GROQ_API_KEY in .env file")

# Cache LLM instances to avoid reinitializing
_llm_cache = {}

# Available Groq models
AVAILABLE_MODELS = {
    "llama-3.3-70b-versatile": {
        "name": "Llama 3.3 70B",
        "description": "Most capable model, best for complex queries",
        "context_length": 8192,
        "speed": "medium"
    },
    "llama-3.1-70b-versatile": {
        "name": "Llama 3.1 70B",
        "description": "Balanced performance and quality",
        "context_length": 8192,
        "speed": "medium"
    },
    "llama-3.1-8b-instant": {
        "name": "Llama 3.1 8B",
        "description": "Fast responses for simple queries",
        "context_length": 8192,
        "speed": "fast"
    
    }
}


def get_llm(model_name="llama-3.3-70b-versatile", temperature=0.7):
    """
    Get or create an LLM instance with the specified model.
    Uses caching to avoid creating multiple instances of the same model.
    
    Args:
        model_name (str): Groq model identifier
        temperature (float): Sampling temperature (0.0 to 1.0)
        
    Returns:
        ChatGroq: Initialized LLM instance
    """
    cache_key = f"{model_name}_{temperature}"
    
    if cache_key not in _llm_cache:
        try:
            _llm_cache[cache_key] = ChatGroq(
                model=model_name,
                temperature=temperature,
                api_key=GROQ_API_KEY
            )
            logger.info(f"Initialized LLM: {model_name} (temperature={temperature})")
        except Exception as e:
            logger.error(f"Error initializing LLM {model_name}: {str(e)}")
            raise
    
    return _llm_cache[cache_key]


def construct_prompt(query, context, system_instruction=None):
    """
    Construct a well-formatted prompt for the LLM.
    
    Args:
        query (str): User's question
        context (str): Retrieved context from documents
        system_instruction (str): Optional custom system instruction
        
    Returns:
        str: Formatted prompt
    """
    if system_instruction is None:
        system_instruction = """You are an AI assistant for a Retrieval-Augmented Generation (RAG) chatbot. Your task is to answer user questions using only the information provided in the context.

Guidelines:
- Only use information from the provided context
- Do not add external knowledge or make assumptions
- If the context is insufficient, acknowledge it clearly
- Provide accurate, clear, and detailed responses
- Cite specific parts of the context when relevant
- Be concise but comprehensive
- Use a professional and helpful tone"""
    
    prompt = f"""{system_instruction}

Context:
{context}

Question: {query}

Answer:"""
    
    return prompt


def generate_response(query, top_chunks, model_name="llama-3.3-70b-versatile", temperature=0.7):
    """
    Generate a response using the specified model.
    
    Pipeline:
    1. Extract context from retrieved chunks
    2. Construct prompt with context and query
    3. Call LLM to generate response
    4. Extract sources from chunks
    5. Return answer and sources
    
    Args:
        query (str): User's question
        top_chunks (list): List of tuples (chunk_text, document_name)
        model_name (str): Groq model identifier
        temperature (float): Sampling temperature
        
    Returns:
        tuple: (answer: str, sources: list)
    """
    logger.info(f"Generating response with model: {model_name}")
    logger.info(f"Query: {query[:100]}...")
    logger.info(f"Number of context chunks: {len(top_chunks)}")
    
    # Validate model
    if model_name not in AVAILABLE_MODELS:
        logger.warning(f"Unknown model {model_name}, falling back to default")
        model_name = "llama-3.3-70b-versatile"
    
    # Extract context from chunks
    if not top_chunks:
        logger.warning("No context chunks provided")
        return "I couldn't find any relevant information in the uploaded documents to answer your question. Please upload documents first.", []
    
    context = "\n\n".join([f"[Source: {doc_name}]\n{chunk}" for chunk, doc_name in top_chunks])
    
    # Construct prompt
    prompt = construct_prompt(query, context)
    
    # Log prompt length for monitoring
    logger.info(f"Prompt length: {len(prompt)} characters")
    
    # Get LLM instance
    try:
        llm = get_llm(model_name, temperature)
    except Exception as e:
        logger.error(f"Failed to get LLM instance: {str(e)}")
        return f"Error: Unable to initialize language model. Please check your API key and try again.", []
    
    # Generate response
    try:
        response = llm.invoke(prompt)
        answer = response.content.strip()
        
        logger.info(f"Response generated successfully ({len(answer)} characters)")
        logger.info(f"Model used: {AVAILABLE_MODELS[model_name]['name']}")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error calling Groq API with model {model_name}: {error_msg}")
        
        # Provide helpful error messages
        if "rate_limit" in error_msg.lower():
            return "Error: Rate limit exceeded. Please wait a moment and try again.", []
        elif "context_length" in error_msg.lower():
            return "Error: Context too long. Try uploading smaller documents or asking a more specific question.", []
        elif "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
            return "Error: Authentication failed. Please check your Groq API key in the .env file.", []
        else:
            return f"Error generating response: {error_msg}", []
    
    # Extract unique sources
    sources = list(set([doc_name for _, doc_name in top_chunks]))
    logger.info(f"Sources: {', '.join(sources)}")
    
    return answer, sources


def get_model_info(model_name):
    """
    Get information about a specific model.
    
    Args:
        model_name (str): Groq model identifier
        
    Returns:
        dict: Model information or None if not found
    """
    return AVAILABLE_MODELS.get(model_name)


def list_available_models():
    """
    List all available models with their details.
    
    Returns:
        dict: Dictionary of model information
    """
    return AVAILABLE_MODELS


# Test response generation
def test_response_generation():
    """
    Test function to verify LLM configuration.
    """
    print("=" * 60)
    print("LLM RESPONSE AGENT - Answer Generation Module")
    print("=" * 60)
    print(f"\nAPI Key Status: {'✓ Configured' if GROQ_API_KEY else '✗ Missing'}")
    if GROQ_API_KEY:
        print(f"API Key (first 10 chars): {GROQ_API_KEY[:10]}...")
    print(f"\nAvailable Models ({len(AVAILABLE_MODELS)}):")
    for model_id, info in AVAILABLE_MODELS.items():
        print(f"\n  {info['name']}")
        print(f"    ID: {model_id}")
        print(f"    Description: {info['description']}")
        print(f"    Context Length: {info['context_length']} tokens")
        print(f"    Speed: {info['speed']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_response_generation()