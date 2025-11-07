# GenAI-Driven-Video-Retrieval-System

## Overview
This project explores the use of **Generative AI** and **Large Language Models (LLMs)** to improve how students interact with recorded lectures.  
Instead of manually searching through hours of video, users can simply ask a question in plain English — for example:

> "Explain the difference between supervised and unsupervised learning."

The system retrieves the most relevant video segment, along with a generated summary and transcript excerpt, providing a more intuitive and efficient learning experience.

---

## Key Features
- **Natural Language Querying** – Users can ask questions in plain text, removing the need for manual keyword search.  
- **Video Retrieval Engine** – Uses **FAISS vector similarity search** to find the most relevant video clip.  
- **Generative Summarisation** – Employs **OpenAI’s GPT model via LangChain** to produce concise summaries of retrieved content.  
- **Transcript Support** – Displays subtitles/transcripts aligned with the retrieved video segment.  
- **Database Integration** – Utilises **MongoDB** to manage video metadata and transcript data efficiently.  
- **Clean, Interactive Frontend** – Built using **React** to provide a simple and responsive user interface.  

---

## Tech Stack

| Component | Technology |
|------------|-------------|
| **Frontend** | React |
| **Backend** | Python (FastAPI / Flask) |
| **AI Integration** | OpenAI GPT models via LangChain |
| **Vector Database** | FAISS |
| **Data Storage** | MongoDB |
| **Other Tools** | Node.js, GitHub, Visual Studio Code |

---

## System Architecture

1. **Transcript Extraction** – Subtitle files are processed to obtain text and timestamps.  
2. **Embedding Generation** – Transcript data is converted into embeddings using an LLM model.  
3. **Vector Indexing** – Embeddings are stored and indexed with **FAISS** for similarity search.  
4. **User Query Processing** – User inputs are embedded and compared against the FAISS index.  
5. **Result Generation** – The top-matching video segment is retrieved, summarised via GPT, and displayed with transcript context.  

---

## Future Work
- Expand to support multi-video retrieval and ranking.  
- Integrate user analytics to track study behaviour.  
- Optimise retrieval speed and embedding efficiency.  
- Add optional voice-based queries for accessibility.  

---

## Acknowledgements
This project was developed as part of the **COMP390 Honours Year Project** at the **University of Liverpool**,  
under the supervision of **Dr Terry Payne**.
