import streamlit as st
from mcp import send_mcp_message, receive_mcp_message
from ingestion_agent import process_document
from retrieval_agent import store_embeddings, retrieve_chunks
from llm_response_agent import generate_response
import os
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, filename="app.log", format="%(asctime)s - %(levelname)s - %(message)s")

# File to store chat history
HISTORY_FILE = "chat_history.json"

# Load chat history from file
def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

# Save chat history to file
def save_chat_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

# Create a new chat session
def create_new_session():
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    return {
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        "title": "New Chat",
        "messages": []
    }

# Coordinator function to manage uploads
def coordinate_upload(file, filename):
    success = process_document(file, filename)
    if success:
        message = receive_mcp_message("RetrievalAgent")
        if message:
            store_embeddings(message["payload"]["chunks"], message["payload"]["document_name"])
        return success
    return False

# Coordinator function to manage queries with model selection
def coordinate_query(query, selected_model):
    top_chunks = retrieve_chunks(query)
    message = receive_mcp_message("LLMResponseAgent")
    if message:
        response, sources = generate_response(
            message["payload"]["query"], 
            message["payload"]["top_chunks"],
            model_name=selected_model  # Pass the selected model
        )
        return response, sources
    return None, None

# Streamlit UI
def main():
    st.set_page_config(page_title="Agentic RAG Chatbot", layout="wide", page_icon="🤖")
    
    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = load_chat_history()
    
    if "current_session" not in st.session_state:
        st.session_state.current_session = create_new_session()
    
    if "messages" not in st.session_state:
        st.session_state.messages = st.session_state.current_session["messages"]
    
    # Sidebar for model selection and chat history
    with st.sidebar:
        st.title("⚙️ Settings")
        
        # Model Selection
        st.subheader("🤖 Model Selection")
        available_models = {
            "Llama 3.3 70B": "llama-3.3-70b-versatile",
            "Llama 3.1 70B": "llama-3.1-70b-versatile",
            "Llama 3.1 8B": "llama-3.1-8b-instant"
        }
        
        selected_model_name = st.selectbox(
            "Choose LLM Model",
            options=list(available_models.keys()),
            index=0,
            help="Select the language model for generating responses"
        )
        
        selected_model = available_models[selected_model_name]
        
        st.markdown("---")
        
        # Chat History Section
        st.subheader("📜 Chat History")
        
        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True):
            # Save current session before creating new one
            if st.session_state.messages:
                st.session_state.current_session["messages"] = st.session_state.messages
                # Update title based on first user message
                if st.session_state.messages:
                    first_msg = next((m for m in st.session_state.messages if m["role"] == "user"), None)
                    if first_msg:
                        st.session_state.current_session["title"] = first_msg["content"][:50] + "..."
                
                # Add to history if not already there
                existing = next((s for s in st.session_state.chat_history 
                               if s["session_id"] == st.session_state.current_session["session_id"]), None)
                if existing:
                    st.session_state.chat_history.remove(existing)
                st.session_state.chat_history.insert(0, st.session_state.current_session)
                save_chat_history(st.session_state.chat_history)
            
            # Create new session
            st.session_state.current_session = create_new_session()
            st.session_state.messages = []
            st.rerun()
        
        # Display chat history
        if st.session_state.chat_history:
            st.markdown("### Previous Chats")
            for idx, session in enumerate(st.session_state.chat_history[:10]):  # Show last 10
                timestamp = datetime.fromisoformat(session["timestamp"]).strftime("%b %d, %H:%M")
                if st.button(
                    f"💬 {session['title']}\n📅 {timestamp}",
                    key=f"history_{idx}",
                    use_container_width=True
                ):
                    # Load selected session
                    st.session_state.current_session = session
                    st.session_state.messages = session["messages"]
                    st.rerun()
        
        st.markdown("---")
        
        # Clear all history button
        if st.button("🗑️ Clear All History", use_container_width=True):
            st.session_state.chat_history = []
            save_chat_history([])
            st.success("History cleared!")
            st.rerun()
    
    # Main content area
    st.title("🤖 Agentic RAG Chatbot")
    st.write("Upload documents and ask questions about their content.")
    
    # Display current model
    st.info(f"**Current Model:** {selected_model_name}")
    
    # Document upload
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
    
    # Chat interface
    # Display the conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 View Sources"):
                    st.markdown("**Sources**: " + ", ".join(set(message["sources"])))
    
    # Chat input
    if prompt := st.chat_input("💬 Ask a question about the documents"):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, sources = coordinate_query(prompt, selected_model)
                
                if response:
                    st.markdown(response)
                    if sources:
                        with st.expander("📚 View Sources"):
                            st.markdown("**Sources**: " + ", ".join(set(sources)))
                    
                    # Add assistant message
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources,
                        "timestamp": datetime.now().isoformat(),
                        "model": selected_model_name
                    })
                    
                    # Update current session
                    st.session_state.current_session["messages"] = st.session_state.messages
                    
                    # Update title if first message
                    if len(st.session_state.messages) == 2:  # First Q&A pair
                        st.session_state.current_session["title"] = prompt[:50] + ("..." if len(prompt) > 50 else "")
                    
                    # Save to history
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
