# GenAI-Driven Lecture Video Retrieval System

A full-stack AI-powered lecture video retrieval system that allows users to ask natural-language questions and receive relevant lecture clips, transcript evidence, timestamps, AI-generated answers and summaries.

This project was developed as part of my COMP390 Honours Year Project at the University of Liverpool.

---

## Overview

Lecture recording platforms often rely on keyword search and manual timeline navigation, which can make it difficult for students to find specific explanations inside long recordings.

This system solves that problem by allowing users to ask questions in plain English, for example:

> "Explain the difference between supervised and unsupervised learning."

The system retrieves the most relevant lecture segment, displays the transcript evidence, links the result to the correct timestamp, and generates a concise AI answer grounded in the lecture content.

---

## Key Features

* **Natural language search** — users can ask questions in plain English instead of relying on exact keywords.
* **Timestamped video retrieval** — returns relevant lecture clips with start and end timestamps.
* **RAG-based answer generation** — retrieves transcript context before generating an AI answer.
* **Whisper/faster-whisper transcription** — converts lecture videos into timestamped WebVTT subtitles.
* **Semantic search with FAISS** — searches transcript chunks using vector similarity.
* **MongoDB storage** — stores transcript chunks, timestamps, video IDs and metadata.
* **Reranking and relevance filtering** — improves retrieval quality and rejects weak matches.
* **No-match handling** — avoids returning irrelevant clips when the lecture content does not answer the query.
* **Automatic lecture ingestion** — detects added, modified or deleted videos and updates the searchable library.
* **React frontend** — provides a chat-style interface with video playback, transcript evidence, summaries and chat history.

---

## Tech Stack

| Area          | Technology                        |
| ------------- | --------------------------------- |
| Frontend      | React, JavaScript, CSS            |
| Backend       | Python, FastAPI                   |
| Database      | MongoDB                           |
| Vector Search | FAISS                             |
| Transcription | Whisper / faster-whisper          |
| Embeddings    | Local sentence-transformer models |
| AI Generation | OpenAI API                        |
| Storage       | Browser localStorage              |
| Tools         | GitHub, VS Code, Node.js          |

---

## How It Works

### 1. Lecture Ingestion

Lecture videos are automatically processed into searchable transcript data.

```text
Lecture Video
    ↓
Whisper/faster-whisper Transcription
    ↓
WebVTT Subtitle File
    ↓
Transcript Parsing
    ↓
Overlapping Transcript Chunks
    ↓
Embedding Generation
    ↓
MongoDB Storage + FAISS Indexing
```

### 2. User Query

When a user asks a question, the system retrieves the most relevant lecture content and generates a grounded response.

```text
User Question
    ↓
Query Embedding
    ↓
FAISS Vector Search
    ↓
MongoDB Chunk Lookup
    ↓
Reranking + Relevance Filtering
    ↓
OpenAI Answer Generation
    ↓
Answer + Summary + Transcript + Timestamped Video Clip
```

---

## Architecture

The system uses a decoupled client-server architecture:

* **React frontend** handles the chat interface, video playback, timestamp cards and local chat history.
* **FastAPI backend** manages retrieval, reranking, relevance filtering, ingestion and answer generation.
* **MongoDB** stores transcript chunks, timestamps, video IDs and metadata.
* **FAISS** performs fast vector similarity search over embedded transcript chunks.
* **OpenAI** generates answers and summaries using retrieved lecture context.

---

## Main Backend Modules

| Module                | Purpose                                                             |
| --------------------- | ------------------------------------------------------------------- |
| `main.py`             | FastAPI application and API endpoints                               |
| `vttParser.py`        | Parses WebVTT subtitles into timestamped transcript segments        |
| `Chunker.py`          | Groups transcript segments into overlapping searchable chunks       |
| `embeddingFactory.py` | Selects the embedding provider                                      |
| `embeddingLocal.py`   | Generates local sentence-transformer embeddings                     |
| `faissIndex.py`       | Builds, saves and loads the FAISS vector index                      |
| `index_manager.py`    | Manages the active FAISS index and mapping                          |
| `search_service.py`   | Retrieves relevant transcript chunks                                |
| `reranker.py`         | Reranks retrieved chunks using relevance signals                    |
| `relevance.py`        | Checks whether a retrieved result is strong enough                  |
| `answerGenerator.py`  | Generates answers and summaries using OpenAI                        |
| `auto_ingest.py`      | Watches the video folder and processes lecture videos automatically |

---

## Testing

The system was tested using a combination of backend test scripts, integration testing and user evaluation.

Test scripts were created for:

* VTT parsing
* transcript chunking
* embedding generation
* FAISS search
* OpenAI connectivity
* RAG answer generation

Integration testing checked that the frontend, backend, database, vector index, answer generation and video playback worked together correctly.

---

## Challenges Solved

* **FAISS always returns a nearest match**
  Added reranking, relevance filtering and no-match handling to avoid weak or irrelevant results.

* **Subtitle segments were too short**
  Implemented overlapping transcript chunks to preserve context.

* **FAISS does not store transcript metadata**
  Used MongoDB alongside FAISS and created a mapping between vector results and transcript documents.

* **Manual lecture processing was inefficient**
  Built automatic ingestion with file watching, file stability checks, manifest tracking and deletion handling.

* **AI answers could be misleading without context**
  Used a RAG approach so answers are generated only from retrieved lecture transcript content.

---

## Outcome

The final system successfully met the main project requirements and achieved an **Overall A grade**. The project demonstrates practical experience with full-stack development, semantic search, vector databases, transcript processing, RAG pipelines and AI-powered educational tools.

---

## Future Improvements

* Add quantitative retrieval metrics such as precision, recall and top-k accuracy.
* Improve transcript quality with post-processing and domain-specific vocabulary handling.
* Replace heuristic reranking with a learned reranking model or cross-encoder.
* Add filters by module, lecture title, topic or date.
* Support larger multi-module lecture libraries.
* Add backend user accounts and cross-device chat history.
* Add confidence indicators for retrieved clips.
* Add voice-based queries for accessibility.

---

## Acknowledgements

Developed as part of the COMP390 Honours Year Project at the University of Liverpool, under the supervision of Dr Terry Payne.
