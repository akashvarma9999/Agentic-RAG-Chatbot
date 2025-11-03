# 🚀 Complete RAG Chatbot - Professional Setup Guide

## 📋 Project Overview

**Agentic RAG Chatbot with Model Context Protocol**

A production-ready Retrieval-Augmented Generation (RAG) chatbot that processes multi-format documents and provides intelligent question-answering capabilities.

### Key Features
- ✅ Multi-format document support (PDF, DOCX, PPTX, CSV, TXT, MD)
- ✅ Vector-based semantic search using FAISS
- ✅ Multiple LLM models (3 Groq models supported)
- ✅ Chat history with persistence
- ✅ Agent-based architecture with MCP communication
- ✅ Interactive Streamlit UI

---

## 🏗️ System Architecture

```
┌─────────────────┐
│  User Interface │  (Streamlit Web App)
│    (app.py)     │
└────────┬────────┘
         │
         ├──────────────────────────────────────┐
         │                                      │
         ▼                                      ▼
┌────────────────┐                    ┌────────────────┐
│  Ingestion     │◄──── MCP ──────────┤  Retrieval     │
│     Agent      │                    │     Agent      │
│                │                    │                │
│ • Parse docs   │                    │ • Embeddings   │
│ • Extract text │                    │ • FAISS index  │
│ • Chunk text   │                    │ • Search       │
└────────┬───────┘                    └────────┬───────┘
         │                                      │
         └──────────────┬───────────────────────┘
                        │
                        ▼
                ┌───────────────┐
                │  LLM Response │
                │     Agent     │
                │               │
                │ • Groq LLMs   │
                │ • 3 models    │
                │ • Generation  │
                └───────────────┘
```

---

## 📁 Complete File Structure

```
Agentic-RAG-Chatbot/
├── app.py                          # Main Streamlit application
├── ingestion_agent.py              # Document processing agent
├── retrieval_agent.py              # Vector search agent
├── llm_response_agent.py           # Answer generation agent
├── mcp.py                          # Agent communication protocol
├── .env                            # Environment variables (API keys)
├── requirements.txt                # Python dependencies
├── chat_history.json               # Chat history storage (auto-created)
├── app.log                         # Application logs (auto-created)
├── vector_store/                   # FAISS vector database (auto-created)
│   ├── embeddings.pkl              # Stored text chunks
│   └── faiss_index.bin             # FAISS index file
└── README.md                       # This file
```

---

## 🛠️ Installation Steps

### Step 1: System Requirements

**Check your Python version:**
```bash
python --version
# Should be Python 3.8 or higher
```

If Python is not installed:
- Download from: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

### Step 2: Clone or Download Project

**Option A: If using Git**
```bash

cd Agentic-RAG-Chatbot-for-Multi-Format-Document-QA-using-Model-Context-Protocol
```

**Option B: Manual Download**
1. Download all the files I provided
2. Create a project folder
3. Place all files in that folder

### Step 3: Replace Files

**Backup your originals (if they exist):**
```bash
# Windows Command Prompt
copy app.py app_original.py
copy llm_response_agent.py llm_response_agent_original.py
copy ingestion_agent.py ingestion_agent_original.py
copy retrieval_agent.py retrieval_agent_original.py
copy mcp.py mcp_original.py
```

**Replace with new files:**
- Rename downloaded files:
  - `app-enhanced.py` → `app.py`
  - `llm-response-agent-full.py` → `llm_response_agent.py`
  - `ingestion-agent.py` → `ingestion_agent.py`
  - `retrieval-agent.py` → `retrieval_agent.py`
  - `mcp-protocol.py` → `mcp.py`

### Step 4: Create Virtual Environment

**Windows:**
```bash
# Navigate to project folder
cd path\to\Agentic-RAG-Chatbot

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

**Linux/Mac:**
```bash
cd path/to/Agentic-RAG-Chatbot
python3 -m venv venv
source venv/bin/activate
```

### Step 5: Install Dependencies

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install all required packages
pip install streamlit
pip install langchain-groq
pip install sentence-transformers
pip install faiss-cpu
pip install python-dotenv
pip install PyPDF2
pip install python-docx
pip install python-pptx
```

Or use requirements file:
```bash
pip install -r requirements.txt
```

### Step 6: Set Up Environment Variables

**Create `.env` file in project root:**

```bash
# Windows (Command Prompt)
echo GROQ_API_KEY=your_groq_api_key_here > .env

# Linux/Mac
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```

**Or create manually:**
1. Create a file named `.env` (with the dot)
2. Add this line:
```
GROQ_API_KEY=gsk_your_actual_key_here
```

**Get Groq API Key:**
1. Go to: https://console.groq.com/
2. Sign up / Login
3. Navigate to "API Keys"
4. Create new key
5. Copy and paste into `.env` file

### Step 7: Verify Installation

**Test each agent individually:**

```bash
# Test Ingestion Agent
python ingestion_agent.py

# Test Retrieval Agent
python retrieval_agent.py

# Test LLM Response Agent
python llm_response_agent.py

# Test MCP Protocol
python mcp.py
```

Each should display information without errors.

---

## ▶️ Running the Application

### Start the Application

```bash
# Make sure virtual environment is activated
# You should see (venv) in prompt

# Run Streamlit app
streamlit run app.py
```

### Expected Output

```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Browser will open automatically showing your chatbot.

---

## 🎯 Using the Application

### 1. **Model Selection**
- Open sidebar (click arrow if collapsed)
- Select from 5 available models:
  - **Llama 3.3 70B** - Best quality, complex queries
  - **Llama 3.1 70B** - Balanced performance
  - **Llama 3.1 8B** - Fast responses

### 2. **Upload Documents**
- Click "Browse files" button
- Select one or multiple files
- Supported formats: PDF, DOCX, PPTX, CSV, TXT, MD
- Wait for "Successfully processed" message

### 3. **Ask Questions**
- Type question in chat input box
- Press Enter or click send
- View response with sources
- Click "View Sources" to see which documents were used

### 4. **Chat History**
- **New Chat**: Click "➕ New Chat" button
- **View History**: See previous conversations in sidebar
- **Load Chat**: Click any history item to reload it
- **Clear All**: Remove all history with "🗑️ Clear All History"

---

## 📊 Agent Details for Presentation

### **Ingestion Agent** (ingestion_agent.py)

**Responsibilities:**
- Multi-format document parsing
- Text extraction from various formats
- Intelligent text chunking with overlap
- Communication with Retrieval Agent via MCP

**Supported Formats:**
- PDF - PyPDF2
- DOCX - python-docx
- PPTX - python-pptx
- CSV - Python csv module
- TXT/MD - Plain text reading

**Chunking Strategy:**
- Default chunk size: 500 characters
- Overlap: 50 characters
- Sentence-boundary aware splitting
- Preserves context between chunks

**Key Functions:**
```python
process_document(file, filename)  # Main entry point
extract_text_from_pdf(file)       # PDF processing
chunk_text(text, chunk_size, overlap)  # Text segmentation
```

---

### **Retrieval Agent** (retrieval_agent.py)

**Responsibilities:**
- Generate embeddings using SentenceTransformer
- Store embeddings in FAISS vector database
- Perform semantic similarity search
- Manage vector store persistence

**Technology Stack:**
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Vector Database**: FAISS (Facebook AI Similarity Search)
- **Storage**: Pickle for metadata, binary for index

**Search Process:**
1. Convert query to embedding
2. Search FAISS index with L2 distance
3. Retrieve top-k most similar chunks
4. Return chunks with document metadata

**Key Functions:**
```python
store_embeddings(chunks, doc_name)  # Add to vector DB
retrieve_chunks(query, top_k=5)     # Semantic search
get_vector_store_stats()            # Statistics
```

---

### **LLM Response Agent** (llm_response_agent.py)

**Responsibilities:**
- Receive query and context from Retrieval Agent
- Construct context-aware prompts
- Generate answers using Groq LLMs
- Handle multiple model support
- Error handling and fallback responses

**Available Models:**

| Model | Context | Speed | Use Case |
|-------|---------|-------|----------|
| Llama 3.3 70B | 8K | Medium | Complex queries |
| Llama 3.1 70B | 8K | Medium | General purpose |
| Llama 3.1 8B | 8K | Fast | Quick answers |
| Mixtral 8x7B | 32K | Fast | Long documents |
| Gemma 2 9B | 8K | Fastest | Simple queries |

**Prompt Engineering:**
- System instruction for RAG behavior
- Context injection from retrieved chunks
- Source attribution
- Clear guidelines for LLM

**Key Functions:**
```python
generate_response(query, chunks, model)  # Main generation
construct_prompt(query, context)         # Prompt building
get_llm(model_name, temperature)         # Model management
```

---

### **MCP Protocol** (mcp.py)

**Purpose:**
Model Context Protocol - standardized communication between agents

**Architecture:**
- Message queue system (in-memory)
- Async-ready design
- Extensible to Redis/RabbitMQ

**Message Format:**
```python
{
    "sender": "AgentName",
    "receiver": "AgentName",
    "payload": { /* agent-specific data */ },
    "timestamp": "ISO-8601",
    "message_id": "unique_id"
}
```

**Communication Flow:**
```
IngestionAgent → RetrievalAgent
    (chunks, document_name)

RetrievalAgent → LLMResponseAgent
    (query, top_chunks)
```

**Key Functions:**
```python
send_mcp_message(message)      # Send message
receive_mcp_message(receiver)  # Receive message
get_mcp_stats()                # Queue statistics
```

---

## 📈 Presenting to Your Manager

### **Demo Flow:**

1. **Introduction** (2 min)
   - Show architecture diagram
   - Explain RAG concept
   - Highlight multi-agent design

2. **Agent Walkthrough** (5 min)
   - Run each agent test independently
   - Show logs and output
   - Explain responsibilities

3. **Live Demo** (8 min)
   - Upload sample document
   - Ask 3-4 questions
   - Show source attribution
   - Switch models to compare
   - Demonstrate chat history

4. **Technical Deep Dive** (5 min)
   - Code walkthrough of one agent
   - Show MCP communication
   - Explain vector search
   - Discuss model selection

### **Key Points to Emphasize:**

✅ **Modular Architecture** - Each agent is independent and testable
✅ **Scalability** - Can replace MCP with production message queue
✅ **Flexibility** - Easy to add new document formats or models
✅ **Production-Ready** - Includes logging, error handling, persistence
✅ **Modern Stack** - FAISS, Transformers, LangChain, Streamlit

### **Technical Highlights:**

- **Embedding Dimension**: 384 (all-MiniLM-L6-v2)
- **Search Algorithm**: L2 distance in FAISS
- **Chunking Strategy**: 500 chars with 50 char overlap
- **Model Options**: 5 Groq LLMs with different characteristics
- **Storage**: Persistent FAISS index + pickle metadata

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError"
```bash
# Activate venv first
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Then install missing package
pip install <package-name>
```

### Issue: "GROQ_API_KEY not found"
```bash
# Check .env file exists
type .env  # Windows
cat .env   # Linux/Mac

# Should show: GROQ_API_KEY=gsk_...
# If not, create it
```

### Issue: "Port 8501 already in use"
```bash
# Kill existing Streamlit
taskkill /F /IM streamlit.exe  # Windows
pkill -f streamlit  # Linux/Mac

# Or use different port
streamlit run app.py --server.port 8502
```

### Issue: "No module named 'mcp'"
```bash
# Make sure you're in the correct directory
dir  # Windows - should show mcp.py
ls   # Linux/Mac - should show mcp.py
```

### Issue: Documents not indexing
```bash
# Check logs
type app.log  # Windows
cat app.log   # Linux/Mac

# Clear vector store and retry
python
>>> from retrieval_agent import clear_vector_store
>>> clear_vector_store()
>>> exit()
```

---

## 📝 Testing Checklist

Before presenting, verify:

- [ ] All agents run individually without errors
- [ ] `.env` file has valid Groq API key
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Streamlit app starts successfully
- [ ] Can upload at least one document
- [ ] Can ask question and get response
- [ ] Can switch models
- [ ] Chat history works
- [ ] Sources are displayed correctly
- [ ] All 5 models are selectable
- [ ] Logs are being written to app.log

---

## 🎓 Understanding the Pipeline

### **Document Upload Flow:**
```
1. User uploads file
2. Streamlit receives file object
3. Ingestion Agent extracts text
4. Text chunked into segments
5. MCP message sent to Retrieval Agent
6. Embeddings created for each chunk
7. Embeddings stored in FAISS index
8. Success message displayed
```

### **Query Flow:**
```
1. User types question
2. Retrieval Agent embeds query
3. FAISS searches for similar chunks
4. Top-k chunks retrieved
5. MCP message sent to LLM Agent
6. Context + query → LLM prompt
7. LLM generates response
8. Response + sources displayed
9. Chat history updated
```

---

## 📞 Support Resources

- **Streamlit Docs**: https://docs.streamlit.io/
- **LangChain Docs**: https://python.langchain.com/
- **FAISS Wiki**: https://github.com/facebookresearch/faiss/wiki
- **Groq Platform**: https://console.groq.com/docs
- **Sentence Transformers**: https://www.sbert.net/

---

## ✅ Quick Start Commands (Copy-Paste Ready)

**Windows Setup:**
```bash
cd path\to\your\project
python -m venv venv
venv\Scripts\activate
pip install streamlit langchain-groq sentence-transformers faiss-cpu python-dotenv PyPDF2 python-docx python-pptx
echo GROQ_API_KEY=your_key_here > .env
streamlit run app.py
```

**Linux/Mac Setup:**
```bash
cd path/to/your/project
python3 -m venv venv
source venv/bin/activate
pip install streamlit langchain-groq sentence-transformers faiss-cpu python-dotenv PyPDF2 python-docx python-pptx
echo "GROQ_API_KEY=your_key_here" > .env
streamlit run app.py
```

---

**🎉 Your RAG chatbot is now ready for presentation!**

Good luck with your manager presentation! 🚀
