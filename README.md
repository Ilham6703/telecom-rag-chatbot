# 🤖 Telecom RAG Chatbot

> A production-ready Retrieval-Augmented Generation (RAG) chatbot for answering questions about **3GPP 5G Core Network Standards**, built using **FastAPI, OpenAI GPT-4o, Hybrid Retrieval (Dense + BM25), Cohere Rerank, Qdrant, and LangSmith**.

---

## 📖 Overview

The Telecom RAG Chatbot is an AI-powered assistant designed to answer questions about **3GPP Technical Specifications** using a grounded Retrieval-Augmented Generation (RAG) pipeline.

Unlike a conventional LLM chatbot, responses are generated only after retrieving relevant information from an indexed telecom knowledge base. If sufficient evidence is unavailable, the chatbot abstains instead of producing unsupported answers.

The current knowledge base is built from:

- **3GPP TS 23.501 – System Architecture for the 5G System**
- **3GPP TS 23.502 – Procedures for the 5G System**

---

# ✨ Features

- 📚 Grounded Retrieval-Augmented Generation (RAG)
- 🔍 Hybrid Retrieval (Dense Vector Search + BM25)
- 🎯 Cohere Rerank for relevance optimization
- 🧠 Session-based conversational memory
- ⚡ Streaming responses
- 🚫 Hallucination-aware response generation
- 📄 DOCX document ingestion pipeline
- ☁️ Qdrant Cloud vector database
- 📊 LangSmith observability and tracing
- 🌐 FastAPI REST API
- 💬 Streamlit web interface
- 🧩 Modular, production-oriented architecture

---

# 🏗 System Architecture

```
                         +----------------------+
                         |   Streamlit Frontend |
                         +----------+-----------+
                                    |
                                    |
                                    ▼
                         +----------------------+
                         |      FastAPI API     |
                         +----------+-----------+
                                    |
                                    ▼
                           LLM Query Router
                           /              \
                  General Chat      Knowledge Query
                                          |
                                          ▼
                               Hybrid Retriever
                              /                 \
                     Dense Search          BM25 Search
                              \                 /
                               \               /
                                ▼
                          Merge & Deduplicate
                                ▼
                        Cohere Reranker
                                ▼
                      Relevance Threshold
                                ▼
                          GPT-4o Generation
                                ▼
                         Streamed Response
```

---

# ⚙ Technology Stack

| Layer | Technology |
|--------|------------|
| Backend | FastAPI |
| Frontend | Streamlit |
| LLM | OpenAI GPT-4o |
| Embeddings | OpenAI Embeddings |
| Vector Database | Qdrant Cloud |
| Sparse Retrieval | BM25 |
| Reranking | Cohere Rerank v3 |
| Observability | LangSmith |
| Memory | Session-based In-Memory |
| Document Parsing | python-docx |
| Language | Python 3.11 |

---

# 📂 Project Structure

```
telecom-rag-chatbot/
│
├── app/
│   ├── api/
│   ├── config/
│   ├── ingestion/
│   ├── retrieval/
│   ├── services/
│   ├── utils/
│   └── observability/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── indexes/
│
├── frontend/
│   └── streamlit_app.py
│
├── scripts/
│   └── ingest.py
│
├── tests/
│
├── evaluation/
│
├── main.py
├── requirements.txt
└── README.md
```

---

# 📚 Knowledge Base

The chatbot currently indexes the following 3GPP Technical Specifications:

- **TS 23.501** – System Architecture for the 5G System
- **TS 23.502** – Procedures for the 5G System

The ingestion pipeline:

1. Parses DOCX documents
2. Splits them into semantically meaningful chunks
3. Generates embeddings
4. Stores vectors in Qdrant
5. Builds a BM25 lexical index

---

# 🔄 RAG Pipeline

### Document Ingestion

- DOCX parsing
- Metadata extraction
- Intelligent chunking
- Embedding generation
- Vector indexing

### Query Processing

Incoming requests are classified into:

- General conversation
- Knowledge-based questions

### Hybrid Retrieval

Knowledge queries use:

- Dense semantic retrieval (Qdrant)
- Sparse lexical retrieval (BM25)

Retrieved results are merged and reranked using Cohere.

### Response Generation

Only the highest-ranked context is provided to GPT-4o.

If no relevant evidence passes the retrieval threshold, the chatbot returns a grounded abstention response instead of generating unsupported information.

---

# 💬 Conversation Memory

The chatbot supports session-based conversational memory.

Features include:

- Browser session isolation
- Last 15 messages retained
- Independent conversation history per session
- No cross-session memory leakage

---

# 📊 Observability

The project integrates **LangSmith** for tracing and observability.

LangSmith provides:

- End-to-end request tracing
- LLM execution monitoring
- Retrieval pipeline visibility
- Prompt inspection
- Token usage analysis
- Latency tracking
- Debugging support for production workflows

# 🧪 Evaluation

The chatbot has been manually evaluated using a curated benchmark covering:

- General conversation
- Session memory
- Telecom definitions
- Network functions
- 5G procedures
- System architecture
- Out-of-domain queries
- Grounded abstention behavior

The evaluation process focused on verifying retrieval quality, response grounding, conversational behavior, and safe abstention when relevant documentation was unavailable.

---

# ⚠ Current Limitations

- Knowledge base is currently limited to **TS 23.501** and **TS 23.502**
- No conversational query rewriting
- No persistent database-backed memory
- Retrieval quality depends on indexed document coverage
- Does not provide explicit citations in responses (planned enhancement)

---

# 🚀 Future Enhancements

- RAGAS-based automated evaluation pipeline
- Source citation and evidence highlighting
- Query rewriting for conversational follow-up questions
- Expanded 3GPP specification coverage
- Metadata-aware retrieval optimization
- Persistent conversation history
- Docker and Kubernetes deployment
- CI/CD integration

---


# 👨‍💻 Author

**Ilham Khan**

AI Engineer | Generative AI | Agentic AI | Retrieval-Augmented Generation (RAG)

- LinkedIn: https://www.linkedin.com/in/ilham-khan-2652a3295


⭐ If you found this project useful, consider giving it a star!