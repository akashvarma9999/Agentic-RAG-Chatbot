# 🎯 **Agentic RAG Chatbot (Multi-Format Document Question Answering)**

# 🚀 **Overview**

This project implements a **RAG-powered chatbot** built on a **multi-agent architecture** using a custom **Model Context Protocol (MCP)**.
It enables **source-cited, contextually accurate answers** from multiple document formats using **hybrid search**, **semantic embeddings**, and **reranking models**—all wrapped in a modern **Streamlit interface**.

---

# 📌 **Key Features**

* 🗂️ **Multi-format document ingestion:** PDF, DOCX, PPTX, CSV, TXT, MD
* 🔍 **Advanced Retrieval Modes:**
  ✓ Semantic Search (FAISS)
  ✓ Keyword Search
  ✓ Hybrid Search (Semantic + Keyword)
* 🎯 **Reranker Support:**
  ✓ BGE Reranker
  ✓ HuggingFace BGE Reranker
* ⚡ **Groq LLM Integration** using *Llama 3.3 70B* and *Llama 3.1 8B*
  🔥 Ultra-fast inference with full source grounding
* 🧩 **Agentic Architecture:**

  * Ingestion Agent
  * Retrieval Agent
  * LLM Response Agent
  * MCP Coordinator
* 📚 **Inline source citations** for transparency
* 💾 **Persistent chat history + session management**
* 🖥️ **Streamlit UI** with model, reranker, and search-mode selectors

---

# 🧠 **System Architecture**

```
                        ┌──────────────────────────┐
                        │      Streamlit UI        │
                        │ - Upload documents       │
                        │ - Select models/modes    │
                        │ - Chat interface         │
                        └───────────┬──────────────┘
                                    │
                                    ▼
                  ┌──────────────────────────────────────┐
                  │  Model Context Protocol (MCP Layer)  │
                  │  Structured message-passing pipeline │
                  └──────────┬───────────────┬──────────┘
                             │               │
                             ▼               ▼
                    ┌────────────┐     ┌──────────────┐
                    │ Ingestion   │     │ Retrieval     │
                    │ Agent       │     │ Agent         │
                    │ - Parse     │     │ - Embeddings  │
                    │ - Chunk     │     │ - FAISS       │
                    └────────────┘     │ - Hybrid Search│
                                        └───────┬────────┘
                                                │
                                                ▼
                                    ┌────────────────────────┐
                                    │ LLM Response Agent     │
                                    │ - Prompt construction  │
                                    │ - Groq LLM inference   │
                                    │ - Source citations     │
                                    └────────────────────────┘
```

---

# 📁 **Project Structure**

```
Agentic-RAG-Chatbot/
│
├── app.py                       # Streamlit UI
├── ingestion_agent.py           # Multi-format parsing + chunking
├── retrieval_agent.py           # FAISS + Hybrid search + rerankers
├── llm_response_agent.py        # LLM generation + citations
├── mcp.py                       # Agent communication protocol
│
├── vector_store/                # FAISS index + embeddings
│   ├── faiss_index.bin
│   └── embeddings.pkl
│
├── chat_history.json            # Saved sessions
├── requirements.txt             
├── .env                          # API key
└── README.md
```

---

# 🛠️ **Installation**

### 1️⃣ Clone the repo

```bash
git clone https://github.com/akashvarma9999/Agentic-RAG-Chatbot.git
cd Agentic-RAG-Chatbot
```

### 2️⃣ Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Add Groq API key

Create `.env`:

```
GROQ_API_KEY=your_api_key_here
```

### 5️⃣ Run the application

```bash
streamlit run app.py
```

---

# 🔍 **Retrieval Modes**

### **✔ Semantic Search**

Based on transformer embeddings + FAISS vector similarity.

### **✔ Keyword Search**

Fast keyword and fuzzy-match search.

### **✔ Hybrid Search (Recommended)**

Combines semantic + keyword + reranking.

---

# 🧬 **Rerankers Supported**

| Reranker            | Description                          |
| ------------------- | ------------------------------------ |
| **None**            | Raw semantic or hybrid results       |
| **BGE Reranker**    | Cross-encoder reranking for accuracy |
| **HF BGE-Reranker** | HuggingFace-powered reranker         |

---

# 🤖 **LLM Support (Groq API)**

| Model                       | Purpose                |
| --------------------------- | ---------------------- |
| **Llama 3.3 70B Versatile** | Best quality responses |
| **Llama 3.1 8B Instant**    | Faster + lightweight   |

---

# 🔧 **Core Agent Modules**

### 🟦 **Ingestion Agent**

* Multi-format text extraction
* Cleaning, chunking (with overlap)
* Sends chunks to Retrieval Agent using MCP

### 🟪 **Retrieval Agent**

* Dynamic embedding model selection
* FAISS vector store
* Semantic, keyword, hybrid search
* Optional reranking

### 🟩 **LLM Response Agent**

* Builds structured prompts
* Calls Groq LLMs
* Generates grounded answers with citations

### 🟨 **MCP (Model Context Protocol)**

* Internal message-passing layer
* Ensures loose coupling & extensibility

---

# 🎓 **Learning Outcomes**

* RAG pipelines and hybrid search engineering
* FAISS optimization + embedding strategies
* Microservice-style agent design (MCP)
* Groq LLM integration
* Streamlit UI engineering
* Error handling + logging + debugging
* Modular and scalable architecture

---

# 🌟 **Future Enhancements**

* Auto-reindexing for updated files
* Database integration (MongoDB / PostgreSQL)
* Multi-language support
* Document summarization agent
* Docker deployment
* GPU-backed FAISS

---

# 🏁 **Conclusion**

This Agentic RAG Chatbot demonstrates how **semantic retrieval**, **reranking**, and **LLMs** can be combined into a reliable, scalable enterprise knowledge system.
The multi-agent architecture ensures **modularity**, **extensibility**, and **clear separation of concerns**, making it suitable for real-world organizational deployment.

---

# 📄 **License**

This project is licensed under the MIT License.

MIT License

Copyright (c) 2025 Gadhiraju Akash Varma

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.

---


