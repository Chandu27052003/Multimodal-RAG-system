# Multimodal RAG System: Research-Style Project Documentation

## Project Structure Summary

The workspace implements a Dockerized microservice-based multimodal Retrieval-Augmented Generation (RAG) platform. The system is organized into eight runtime services inside `services/`: `ingestion`, `preprocessing`, `embedding`, `vector_store`, `retrieval`, `generation`, `gateway`, and `ui`. Supporting project files include `docker-compose.yml` for orchestration, per-service `Dockerfile` and `requirements.txt` files, `CHECKLIST.md` for implementation status tracking, and `Documentation.txt` as an earlier design-oriented narrative.

The functional pipeline is divided into two major paths. The indexing path accepts documents, URLs, audio, and YouTube content; extracts or transcribes text; normalizes and chunks the content; converts chunks into vector embeddings; and stores vectors with metadata in ChromaDB. The query path normalizes a user query, creates a query embedding, retrieves candidate chunks from the vector database, reranks them using an NVIDIA reranking model, assembles a bounded context window, and generates a grounded natural-language answer. The Streamlit interface communicates only with the API gateway, while the gateway orchestrates all downstream services through HTTP APIs.

## 1. Abstract

This project presents a multimodal knowledge retrieval and question-answering system built using a microservice architecture. The platform supports ingestion of heterogeneous data sources, including PDF documents, DOCX files, plain text, HTML content, webpages, uploaded audio, and YouTube videos. After ingestion, the system applies text normalization and sentence-aware chunking, generates dense vector embeddings using NVIDIA NIM APIs, and persists the resulting representations in a ChromaDB vector store. At query time, the system transforms user questions into embeddings, retrieves semantically similar chunks, reranks them using a neural reranker, and forwards the grounded context to a large language model for final answer generation. The overall design combines multimodal ingestion, vector search, neural reranking, and LLM-based response generation inside a Dockerized service mesh. The resulting system demonstrates a practical implementation of retrieval-augmented generation for enterprise-style knowledge base construction and grounded question answering.

## 2. Introduction

Modern knowledge-intensive applications require reliable access to information distributed across heterogeneous sources such as reports, notes, webpages, and spoken media. Conventional keyword-based search often fails to capture semantic similarity, while standalone large language models may generate plausible but unsupported responses when asked domain-specific questions. Retrieval-Augmented Generation addresses this limitation by retrieving external evidence first and then conditioning the language model on that evidence.

The present project implements a multimodal RAG system that extends classical document search by supporting audio transcription and YouTube-based knowledge ingestion in addition to standard textual documents. The implementation adopts a microservice architecture to isolate ingestion, preprocessing, embedding, storage, retrieval, generation, orchestration, and user interaction concerns. This separation improves maintainability and allows individual modules to evolve independently. The project therefore serves both as a functional software system and as an applied demonstration of contemporary semantic retrieval architecture.

## 3. Objectives of the Project

The main objectives of the project are as follows:

1. To build a unified platform for ingesting heterogeneous knowledge sources, including text documents, webpages, audio files, and YouTube videos.
2. To normalize and segment raw content into semantically meaningful chunks suitable for embedding and retrieval.
3. To generate dense vector embeddings using an external embedding service based on NVIDIA NIM.
4. To store document chunks and metadata in a persistent vector database for semantic search.
5. To retrieve, rerank, and assemble relevant evidence for grounded question answering.
6. To generate concise responses using a large language model constrained by retrieved context.
7. To expose the full workflow through a public API gateway and a user-facing Streamlit interface.
8. To package the full stack in Docker containers for reproducible deployment.

## 4. Literature Review

Retrieval-Augmented Generation has emerged as a prominent paradigm for grounding language model outputs in external corpora. The core idea, formalized by Lewis et al., combines parametric generation with non-parametric retrieval to improve factuality and domain adaptation. Dense passage retrieval methods, such as those introduced by Karpukhin et al., further improved semantic search by embedding queries and documents into a shared vector space rather than relying solely on lexical overlap.

Subsequent systems commonly introduced a second-stage reranking step, frequently using cross-encoder or cross-attention architectures, to improve precision over initial dense retrieval. In practical industry deployments, vector databases such as ChromaDB, FAISS, Milvus, and similar systems are used to persist embeddings and support scalable approximate nearest-neighbor search. At the same time, multimodal information processing has become increasingly important because organizational knowledge is often distributed across written and spoken artifacts. Speech-to-text systems such as Deepgram make it possible to incorporate audio sources into a text-centric retrieval pipeline.

The present project reflects these developments. Its implemented architecture follows a dense retrieval plus neural reranking pipeline, uses a vector database for persistence, and extends the standard text-only RAG pattern with audio and YouTube transcription workflows. However, some advanced features anticipated in broader RAG literature, such as temporal reasoning, hierarchical summarization, and observability instrumentation, remain scaffolded rather than fully implemented in the current codebase.

## 5. System Overview

The system is a multimodal RAG platform composed of eight services:

1. `ingestion`: parses files, URLs, audio, and YouTube inputs into raw text plus metadata.
2. `preprocessing`: normalizes text and performs sentence-aware chunking with overlap.
3. `embedding`: calls NVIDIA NIM embedding APIs to convert text into 2048-dimensional vectors.
4. `vector_store`: persists vectors, documents, and metadata in ChromaDB collections.
5. `retrieval`: embeds queries, performs vector search, reranks candidates, and builds context.
6. `generation`: calls an OpenAI-compatible NVIDIA endpoint to generate grounded answers.
7. `gateway`: exposes public APIs and orchestrates end-to-end indexing and query execution.
8. `ui`: provides a Streamlit-based frontend for end users.

At runtime, these services are connected through Docker Compose on a shared bridge network. The gateway is the principal public backend entry point, while the UI uses the gateway for all interactions. ChromaDB persists collection data on disk, enabling knowledge base contents to survive container restarts.

[FIGURE 1: Overall System Architecture Diagram]

The diagram should include the Streamlit UI, API Gateway, Ingestion Service, Preprocessing Service, Embedding Service, Vector Store Service, Retrieval Service, Generation Service, external NVIDIA NIM APIs, external Deepgram API, and persistent ChromaDB storage. Arrows should show data flow from the UI to the gateway, from the gateway to downstream services during indexing and query execution, and from the vector store to disk-backed storage. Separate arrows should indicate external calls to Deepgram for transcription and NVIDIA endpoints for embeddings, reranking, and generation.

## 6. Methodology

The implementation uses a pipeline-oriented methodology divided into indexing and querying phases.

During indexing, content is first converted into text through specialized parsers. The resulting text is then normalized to remove formatting artifacts and segmented into overlapping sentence-based chunks. Each chunk is embedded as a dense vector and stored together with its source metadata. During querying, the user question is normalized and embedded using the same embedding model, ensuring compatibility between query and document vectors. Candidate chunks are retrieved through vector similarity search, reranked using a dedicated neural reranker, assembled into a bounded context window, and then supplied to a generation model for grounded answer synthesis.

From a software engineering perspective, the project adopts a microservice methodology. Each service owns a single stage of the pipeline and communicates over REST APIs. This design simplifies modular development and allows independent scaling or substitution of services. The codebase also uses environment-driven configuration, making the stack portable across local and containerized deployments.

## 7. System Architecture

The architecture is built around orchestrated microservices. The gateway delegates specialized tasks to downstream services rather than embedding all logic inside one monolith.

### 7.1 Indexing Architecture

1. A user uploads a file, audio clip, URL, or YouTube link through the UI or an API client.
2. The gateway forwards the request to the ingestion service.
3. The ingestion service extracts text and assigns metadata such as `doc_id`, `source_type`, filename, URL, and parser-specific extra attributes.
4. The gateway forwards the extracted text to preprocessing.
5. Preprocessing cleans the text and generates overlapping chunks.
6. The gateway sends chunk texts to the embedding service.
7. The embedding service calls NVIDIA NIM and returns embedding vectors.
8. The gateway stores vectors, chunk texts, and metadata in the vector store service.

### 7.2 Query Architecture

1. A user submits a natural-language query.
2. The gateway forwards the request to the retrieval service.
3. Retrieval normalizes the query and obtains a query embedding from the embedding service.
4. Retrieval performs vector similarity search against the vector store.
5. Retrieved candidates are reranked using an NVIDIA reranking endpoint.
6. The top reranked chunks are assembled into a bounded context block.
7. The gateway sends query plus context to the generation service.
8. The generation service prompts the LLM and returns a grounded answer and token usage statistics.

[FIGURE 2: Indexing Pipeline Diagram]

The diagram should depict the path `UI/API Client -> Gateway -> Ingestion -> Preprocessing -> Embedding -> Vector Store`. It should show that metadata is created during ingestion, inherited during preprocessing, and stored with vectors in ChromaDB collections. It should also indicate that audio and YouTube ingestion pass through transcription before continuing into the same text pipeline.

[FIGURE 3: Query Pipeline Diagram]

The diagram should depict the path `UI/API Client -> Gateway -> Retrieval -> Embedding -> Vector Store -> Reranker -> Context Builder -> Generation -> Gateway -> UI/API Client`. The figure should show candidate retrieval first, followed by reranking, followed by answer generation. It should also label the context token limit enforced before generation.

## 8. System Design

### 8.1 Module Design

The major modules are summarized below:

- `services/ingestion/app/router.py`: central dispatch logic for file, URL, and YouTube ingestion.
- `services/ingestion/app/parsers/`: specialized parsers for PDF, DOCX, text, HTML, URL, audio, and YouTube sources.
- `services/preprocessing/app/normalizer.py`: removes tags, control characters, and whitespace artifacts.
- `services/preprocessing/app/chunker.py`: performs sentence-aware chunking using NLTK tokenization and word-based overlap.
- `services/embedding/app/embedder.py`: batches requests to the NVIDIA embeddings endpoint.
- `services/vector_store/app/store.py`: wraps ChromaDB persistent collections, query, and deletion operations.
- `services/retrieval/app/retriever.py`: obtains query embeddings and performs vector search.
- `services/retrieval/app/reranker.py`: reranks retrieved chunks using NVIDIA reranking.
- `services/retrieval/app/context_builder.py`: builds the final context window under a token budget.
- `services/generation/app/generator.py`: constructs prompts and calls the LLM endpoint.
- `services/gateway/app/orchestrator.py`: coordinates complete workflows across services.
- `services/ui/app.py`: provides the query, upload, audio, YouTube, and knowledge base management interface.

### 8.2 Data Design

The data model is chunk-centric. Each stored unit includes:

1. A unique chunk identifier such as `doc_xxx_chunk_0000`.
2. Parent document metadata including `doc_id`.
3. Source metadata such as filename, URL, source type, and chunk index.
4. Raw chunk text.
5. A 2048-dimensional embedding vector.

[TABLE 1: Core Runtime Data Objects]

The table should include columns for `Object Name`, `Origin Service`, `Key Fields`, and `Purpose`. Suggested rows include `DocumentMetadata`, `IngestedDocument`, `ChunkResult`, `EmbeddingResult`, `RetrievedChunk`, and `GenerateResponse`.

### 8.3 API Design

The gateway exposes public endpoints such as:

1. `POST /api/ingest/file`
2. `POST /api/ingest/url`
3. `POST /api/ingest/youtube`
4. `POST /api/query`
5. `GET /api/knowledge-base/collections`
6. `GET /api/knowledge-base/`
7. `DELETE /api/knowledge-base/{doc_id}`
8. `GET /health`
9. `GET /health/services`

Internal services expose their own narrower APIs for parsing, preprocessing, embedding, storage, retrieval, and generation. This layered API design ensures that clients interact with a stable public interface while service internals remain modular.

[TABLE 2: Public and Internal API Endpoints]

The table should include columns for `Service`, `Endpoint`, `Method`, `Input`, and `Output`. It should cover the gateway endpoints above plus important internal endpoints such as `/ingest/parse`, `/preprocess/`, `/embed/batch`, `/search`, `/retrieve/`, and `/generate/`.

## 9. Hardware Requirements

Because the project depends on external hosted AI APIs for embeddings, reranking, transcription, and generation, the local hardware requirements are moderate compared with fully self-hosted LLM stacks. A representative deployment can operate on the following baseline:

1. 64-bit processor with at least 2 CPU cores.
2. 8 GB RAM minimum, with 16 GB recommended for smoother Docker-based multitasking.
3. 10 GB or more of free disk space for Docker images, uploaded files, logs, and vector database persistence.
4. Stable internet connectivity for NVIDIA NIM, Deepgram, and YouTube retrieval.
5. Audio decoding support through `ffmpeg`, installed inside the ingestion container.

No dedicated GPU is required in the current implementation because model inference is outsourced to cloud-hosted endpoints.

## 10. Software Requirements

The software stack inferred from the repository includes:

1. Operating system: macOS, Linux, or Windows with Docker support.
2. Python 3.11 runtime.
3. Docker and Docker Compose.
4. FastAPI and Uvicorn for backend APIs.
5. Streamlit for the user interface.
6. ChromaDB for persistent vector storage.
7. NLTK for sentence tokenization.
8. PyPDF2 and `python-docx` for document parsing.
9. BeautifulSoup for HTML cleaning.
10. `yt-dlp` and `ffmpeg` for YouTube audio extraction.
11. `requests` and `httpx` for internal and external HTTP communication.
12. OpenAI Python SDK configured against NVIDIA's OpenAI-compatible endpoint.
13. Environment variables for NVIDIA and Deepgram API credentials.

[TABLE 3: Software Stack and Role Mapping]

The table should include columns for `Technology`, `Version Source`, `Used In`, and `Role`. Representative entries should include FastAPI, Streamlit, ChromaDB, NLTK, Deepgram, NVIDIA NIM, OpenAI SDK, `yt-dlp`, and Docker Compose.

## 11. Working of the System

The working of the system can be explained through two operational scenarios.

### 11.1 Document and Media Indexing

When a user uploads a file, the gateway sends the payload to the ingestion service. The ingestion service first determines the source type from the filename extension. PDF files are parsed using `PyPDF2`, DOCX files are parsed through `python-docx`, text files are decoded through a multi-encoding fallback strategy, and HTML files are cleaned using BeautifulSoup. Audio files are sent to Deepgram for transcription, while YouTube links are first downloaded as audio using `yt-dlp` and `ffmpeg`, then transcribed in the same way.

The extracted text is passed to preprocessing, which removes HTML/script artifacts, control characters, and inconsistent whitespace. NLTK sentence tokenization is then used to group sentences into overlapping chunks based on configurable word-count thresholds. The gateway forwards chunk texts to the embedding service, which batches requests to NVIDIA's embedding endpoint and returns vectors. Finally, the vector store saves chunk IDs, vectors, documents, and metadata into a named ChromaDB collection.

### 11.2 Grounded Question Answering

When a user asks a question, the query is sent through the gateway to the retrieval service. The retrieval service normalizes the query, obtains a query embedding, and performs dense vector search against the specified collection. The top retrieved candidates are then passed to a reranking API, which assigns stronger relevance scores using pairwise query-passage evaluation. The context builder concatenates top reranked chunks while respecting a context token limit. This context block, together with the query, is submitted to the generation service. The generator uses a system prompt that explicitly instructs the model to answer only from provided context, cite sources when possible, and avoid unsupported claims. The generated answer is returned to the caller along with source chunks and usage statistics.

[FIGURE 4: End-to-End Execution Flow]

The diagram should show both the indexing and query cycles in one figure. It should emphasize that all user interactions pass through the gateway, that the vector store is the persistence backbone, and that external AI providers are used for embeddings, reranking, transcription, and generation.

## 12. Applications of the System

The implemented system can be applied in several domains:

1. Institutional knowledge base search over internal reports and notes.
2. Lecture, interview, or meeting transcription indexing for later question answering.
3. Research material aggregation from PDFs, webpages, and recorded explanations.
4. Media-assisted document discovery where audio and YouTube content need to be searchable as text.
5. Prototype semantic search and Q&A systems for enterprise or academic settings.

## 13. Advantages

The current design offers several advantages:

1. Modular microservice decomposition improves maintainability and service isolation.
2. Multimodal ingestion broadens the knowledge sources beyond text-only corpora.
3. Dense retrieval improves semantic search quality over keyword-only methods.
4. Neural reranking improves precision after broad vector retrieval.
5. Grounded generation reduces hallucination risk by conditioning the LLM on retrieved evidence.
6. ChromaDB persistence enables reusable collections across sessions.
7. Dockerized deployment simplifies reproducibility and environment setup.
8. The Streamlit UI makes the platform accessible without requiring direct API usage.

## 14. Limitations

The repository also reveals several practical limitations:

1. Summarization is planned but not implemented; the corresponding files are placeholders.
2. Temporal filtering is scaffolded but not implemented in retrieval.
3. Video file parsing is deferred, with only a placeholder module present.
4. Observability is limited to basic logging; no centralized metrics or tracing are implemented.
5. The system depends heavily on external cloud APIs, requiring internet access and valid API keys.
6. ChromaDB is suitable for prototyping and moderate workloads, but large-scale distributed retrieval concerns are not addressed in the current implementation.
7. Collection and metadata management are functional but relatively simple, without sophisticated access control or schema governance.
8. Some earlier documentation in the workspace describes aspirational capabilities not yet reflected in executable code.

## 15. Future Improvements

Several future improvements follow naturally from the current codebase:

1. Implement hierarchical summarization in the generation service and expose it through the gateway and UI.
2. Complete temporal query detection and metadata-based date filtering.
3. Add full video file ingestion with audio extraction beyond YouTube-specific handling.
4. Improve metadata richness by preserving timestamps, page spans, and section headers more systematically.
5. Introduce authentication, authorization, and collection-level access controls.
6. Add request tracing, structured logging, and performance dashboards.
7. Expand testing coverage with explicit integration and service contract tests inside the repository.
8. Support alternate vector backends such as FAISS or distributed vector databases for larger deployments.
9. Add asynchronous job execution and queues for long-running ingestion workflows.
10. Introduce citation formatting and answer verification layers for more rigorous grounded responses.

[TABLE 4: Proposed Future Enhancements]

The table should include columns for `Enhancement`, `Current Status`, `Expected Benefit`, and `Affected Services`. Example rows include `Summarization`, `Temporal Filtering`, `Video Parsing`, `Observability`, `Auth Layer`, and `Alternative Vector Backend`.

## 16. Conclusion

This project implements a practical multimodal Retrieval-Augmented Generation system using a clean microservice architecture. The repository demonstrates a coherent end-to-end pipeline from heterogeneous content ingestion to grounded answer generation. Its strongest contributions are the integration of text and speech-derived content into a unified vector search workflow, the use of neural reranking to improve retrieval quality, and a deployment model that is straightforward to reproduce with Docker Compose.

At the same time, the codebase honestly reflects a work in progress rather than a finished research platform. Features such as summarization, temporal reasoning, advanced observability, and richer governance remain future work. Even so, the implemented modules form a technically sound foundation for further academic experimentation, product prototyping, or capstone-level system demonstration in the area of semantic retrieval and grounded AI assistants.

## 17. References

1. Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Kuhn, H., Lewis, M., Yih, W., Rocktaschel, T., Riedel, S., and Kiela, D. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *Advances in Neural Information Processing Systems*.
2. Karpukhin, V., Oguz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., and Yih, W. (2020). Dense Passage Retrieval for Open-Domain Question Answering. *Proceedings of EMNLP*.
3. Reimers, N., and Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *Proceedings of EMNLP-IJCNLP*.
4. FastAPI Documentation. Available at: [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
5. Streamlit Documentation. Available at: [https://docs.streamlit.io/](https://docs.streamlit.io/)
6. Chroma Documentation. Available at: [https://docs.trychroma.com/](https://docs.trychroma.com/)
7. NVIDIA NIM Documentation. Available at: [https://docs.nvidia.com/nim/](https://docs.nvidia.com/nim/)
8. Deepgram API Documentation. Available at: [https://developers.deepgram.com/](https://developers.deepgram.com/)
9. NLTK Documentation. Available at: [https://www.nltk.org/](https://www.nltk.org/)
10. yt-dlp Documentation. Available at: [https://github.com/yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp)
11. PyPDF2 Documentation. Available at: [https://pypdf2.readthedocs.io/](https://pypdf2.readthedocs.io/)
12. python-docx Documentation. Available at: [https://python-docx.readthedocs.io/](https://python-docx.readthedocs.io/)
