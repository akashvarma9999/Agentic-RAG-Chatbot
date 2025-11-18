import streamlit as st
from mcp import send_mcp_message, receive_mcp_message
from ingestion_agent import process_document
from retrieval_agent import (
    store_embeddings,
    retrieve_chunks,
    keyword_search,
    rerank_chunks,
    clear_vector_store
)
from llm_response_agent import generate_response
import os
import json
from datetime import datetime
import logging

# Hugging Face imports
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

logging.basicConfig(level=logging.INFO, filename="app.log", format="%(asctime)s - %(levelname)s - %(message)s")
HISTORY_FILE = "chat_history.json"


def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_chat_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def create_new_session():
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "title": "New Chat",
        "messages": []
    }

def coordinate_upload(file, filename):
    embedding_model_name = st.session_state.get('embedding_model_name', "all-MiniLM-L6-v2")
    print("UPLOAD: Using embedding model:", embedding_model_name)
    success = process_document(file, filename, embedding_model_name)
    if success:
        message = receive_mcp_message("RetrievalAgent")
        if message:
            store_embeddings(
                message["payload"]["chunks"],
                message["payload"]["document_name"],
                embeddings=message["payload"].get("embeddings"),
                embedding_model_name=embedding_model_name
            )
        return success
    return False

@st.cache_resource
def load_hf_reranker_model(model_name):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.eval()
    return tokenizer, model

def hf_rerank_chunks(query, chunks, reranker_model_name):
    tokenizer, model = load_hf_reranker_model(reranker_model_name)
    # Prepare input pairs for reranking: (query, chunk_text)
    inputs = tokenizer(
        [query] * len(chunks),
        [chunk[0] if isinstance(chunk, tuple) else chunk for chunk in chunks],
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )
    with torch.no_grad():
        outputs = model(**inputs)
        # For BGE rerankers, relevant class usually index 0
        scores = outputs.logits[:, 0].cpu().numpy()
    scored_chunks = list(zip(chunks, scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    reranked_chunks = [sc[0] for sc in scored_chunks]
    return reranked_chunks

def coordinate_query(query, selected_model, embedding_model_name, reranker_model_name, query_mode):
    def rerank_dispatch(query, chunks, reranker_model_name):
        if reranker_model_name == "BAAI/bge-reranker-base":
            return hf_rerank_chunks(query, chunks, reranker_model_name)
        elif reranker_model_name:
            return rerank_chunks(query, chunks, reranker_model_name)
        else:
            return chunks

    # --- QUERY MODE HANDLING ---
    if query_mode == "Semantic":
        top_chunks = retrieve_chunks(query, embedding_model_name)
        reranked_chunks = rerank_dispatch(query, top_chunks, reranker_model_name)
        if not reranked_chunks:
            return "No semantic matches found.", []

    elif query_mode == "Keyword":
        keyword_chunks = keyword_search(query)
        logging.info(f"[Keyword Mode] Found {len(keyword_chunks)} keyword chunks for query: {query}")
        if not keyword_chunks:
            return "No keyword matches found in document chunks.", []

        # Merge top few keyword chunks
        num_chunks = min(5, len(keyword_chunks))
        merged_text = "\n\n".join([chunk for chunk, _ in keyword_chunks[:num_chunks]])
        merged_chunks = [(merged_text, "keyword_matches")]
        reranked_chunks = merged_chunks

    elif query_mode == "Hybrid":
        semantic_chunks = retrieve_chunks(query, embedding_model_name)
        reranked_sem = rerank_dispatch(query, semantic_chunks, reranker_model_name)
        keyword_chunks = keyword_search(query)
        unique = {(c, d) for (c, d) in reranked_sem + keyword_chunks}
        reranked_chunks = list(unique)[:5]
        if not reranked_chunks:
            return "No matches found with semantic or keyword search.", []

    else:
        # Default to semantic mode if unspecified
        top_chunks = retrieve_chunks(query, embedding_model_name)
        reranked_chunks = rerank_dispatch(query, top_chunks, reranker_model_name)
        if not reranked_chunks:
            return "No semantic matches found.", []

    # --- FIXED RESPONSE GENERATION ---
    message = receive_mcp_message("LLMResponseAgent")
    if message:
        query_to_send = message["payload"].get("query", query)
        logging.info("[MCP] Received query from LLMResponseAgent.")
    else:
        query_to_send = query
        logging.info("[Fallback] Using user query directly for generate_response.")

    response, sources = generate_response(
        query_to_send,
        reranked_chunks,
        model_name=selected_model,
        embedding_model_name=embedding_model_name
    )

    logging.info(f"[LLM Response] Generated response length: {len(response) if response else 0}")
    return response, sources



def main():
    st.set_page_config(page_title="Agentic RAG Chatbot", layout="wide", page_icon="🤖")

    # Session state setup
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = load_chat_history()
    if "current_session" not in st.session_state:
        st.session_state.current_session = create_new_session()
    if "messages" not in st.session_state:
        st.session_state.messages = st.session_state.current_session["messages"]
    if "prev_embedding_model_name" not in st.session_state:
        st.session_state.prev_embedding_model_name = None

    with st.sidebar:
        st.title("⚙️ Settings")
        st.subheader("🤖 Model Selection")
        available_models = {
            "Llama 3.3 70B": "llama-3.3-70b-versatile",
            "Llama 3.1 8B": "llama-3.1-8b-instant"
        }
        embedding_models = {
            "MiniLM": "all-MiniLM-L6-v2",
            "MPNET": "all-mpnet-base-v2",
            "DistilBERT": "distilbert-base-nli-stsb-mean-tokens"
        }
        reranker_models = {
            "None": None,
            "BGE-Reranker": "BAAI/bge-reranker-base",
            "HF BGE-Reranker": "BAAI/bge-reranker-base"
        }
        query_modes = ["Semantic", "Keyword", "Hybrid"]
        selected_model_name = st.selectbox("Choose LLM Model", list(available_models.keys()), index=0)
        selected_model = available_models[selected_model_name]
        selected_embedding_model_name = st.selectbox("Choose Embedding Model", list(embedding_models.keys()), index=0)
        embedding_model_name = embedding_models[selected_embedding_model_name]
        selected_reranker_model_name = st.selectbox("Choose Reranker", list(reranker_models.keys()), index=0)
        reranker_model_name = reranker_models[selected_reranker_model_name]
        selected_query_mode = st.radio("Choose Query Mode", query_modes, index=0)
        st.session_state['embedding_model_name'] = embedding_model_name
        st.session_state['reranker_model_name'] = reranker_model_name
        st.session_state['query_mode'] = selected_query_mode

        if st.session_state.prev_embedding_model_name != embedding_model_name:
            clear_vector_store()
            st.session_state.prev_embedding_model_name = embedding_model_name

        st.markdown("---")
        st.subheader("📜 Chat History")
        if st.button("➕ New Chat", use_container_width=True):
            if st.session_state.messages:
                st.session_state.current_session["messages"] = st.session_state.messages
                if st.session_state.messages:
                    first_msg = next((m for m in st.session_state.messages if m["role"] == "user"), None)
                    if first_msg:
                        st.session_state.current_session["title"] = first_msg["content"][:50] + "..."
                existing = next((s for s in st.session_state.chat_history
                                if s["session_id"] == st.session_state.current_session["session_id"]), None)
                if existing:
                    st.session_state.chat_history.remove(existing)
                st.session_state.chat_history.insert(0, st.session_state.current_session)
                save_chat_history(st.session_state.chat_history)
            st.session_state.current_session = create_new_session()
            st.session_state.messages = []
            st.rerun()
        if st.session_state.chat_history:
            st.markdown("### Previous Chats")
            for idx, session in enumerate(st.session_state.chat_history[:10]):
                timestamp = datetime.fromisoformat(session["timestamp"]).strftime("%b %d, %H:%M")
                if st.button(
                    f"💬 {session['title']}\n📅 {timestamp}",
                    key=f"history_{idx}",
                    use_container_width=True
                ):
                    st.session_state.current_session = session
                    st.session_state.messages = session["messages"]
                    st.rerun()
        st.markdown("---")
        if st.button("🗑️ Clear All History", use_container_width=True):
            st.session_state.chat_history = []
            save_chat_history([])
            st.success("History cleared!")
            st.rerun()

    st.title("🤖 Agentic RAG Chatbot")
    st.write("Upload documents and ask questions about their content.")
    st.info(
        f"**Current Model:** {selected_model_name}"
        f"\n**Embedding Model:** {selected_embedding_model_name}"
        f"\n**Reranker:** {selected_reranker_model_name}"
        f"\n**Query Mode:** {selected_query_mode}"
    )

    uploaded_files = st.file_uploader(
        "📁 Upload Documents",
        accept_multiple_files=True,
        type=["pdf", "pptx", "csv", "docx", "txt", "md"]
    )
    if uploaded_files:
        for file in uploaded_files:
            with st.spinner(f"Processing {file.name}..."):
                if coordinate_upload(file, file.name):
                    st.success(f"✅ Successfully processed {file.name}")
                else:
                    st.error(f"❌ Failed to process {file.name}")

    st.markdown("---")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 View Sources"):
                    st.markdown("**Sources**: " + ", ".join(set(message["sources"])))
    if prompt := st.chat_input("💬 Ask a question about the documents"):
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, sources = coordinate_query(
                    prompt, selected_model, embedding_model_name, reranker_model_name, selected_query_mode
                )
                print(f"[DEBUG] LLM Response: {response}")
                if response and response.strip() and response.strip().lower() not in [
                    "no relevant information found.",
                    "no keyword matches found in document chunks.",
                    "no matches found with semantic or keyword search."
                ]:
                    st.markdown(response)
                    if sources:
                        with st.expander("📚 View Sources"):
                            st.markdown("**Sources**: " + ", ".join(set(sources)))
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources,
                        "timestamp": datetime.now().isoformat(),
                        "model": selected_model_name
                    })
                    st.session_state.current_session["messages"] = st.session_state.messages
                    if len(st.session_state.messages) == 2:
                        st.session_state.current_session["title"] = prompt[:50] + ("..." if len(prompt) > 50 else "")
                    existing = next((s for s in st.session_state.chat_history
                                    if s["session_id"] == st.session_state.current_session["session_id"]), None)
                    if existing:
                        st.session_state.chat_history.remove(existing)
                    st.session_state.chat_history.insert(0, st.session_state.current_session)
                    save_chat_history(st.session_state.chat_history)
                else:
                    st.error("❌ No relevant information found.")

if __name__ == "__main__":
    main()
