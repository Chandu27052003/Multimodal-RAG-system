## Project Title & Summary

# Multimodal RAG System

This project implements a sophisticated multimodal Retrieval-Augmented Generation (RAG) system designed to provide reliable access to information from a diverse set of sources. Its core purpose is to extend traditional document search by integrating audio transcription and YouTube-based knowledge ingestion alongside standard textual documents. By first retrieving relevant external evidence and then conditioning a language model on this evidence, the system aims to generate accurate and contextually supported responses, overcoming the limitations of conventional keyword search and unaugmented large language models. The system facilitates both the comprehensive indexing of various content types and the intelligent querying for grounded natural-language answers.

The system is engineered with a microservice architecture, employing Docker for containerization and consistent deployment across environments. Key services include ingestion, preprocessing, embedding, vector storage (ChromaDB), retrieval, generation, and an API gateway built with FastAPI. Distinct features include a hierarchical document summarization workflow for long texts and temporal query processing to filter results based on time-related metadata. The multimodal ingestion pipeline handles documents, URLs, audio, and YouTube content, processing them into vector embeddings. Queries are processed through embedding, vector retrieval, reranking with an NVIDIA model, and ultimately generate grounded answers, all orchestrated via HTTP APIs and accessible through a Streamlit-based user interface.

---

## Features

*   **API-First Design**:
    *   Exposes all core system functionalities via a **FastAPI backend API**.
    *   Provides dedicated endpoints for:
        *   **Document Ingestion**: Upload and process various text documents.
        *   **Audio Ingestion**: Process audio files (beyond YouTube-specific handling).
        *   **Webpage Indexing**: Ingest content directly from specified web URLs.
        *   **Knowledge Base Querying**: Facilitates information retrieval from the indexed knowledge base.
    *   Features **Interactive API Documentation** (Swagger UI/OpenAPI) automatically generated for easy testing and integration.

*   **Advanced Document Preprocessing Pipeline**:
    *   **Text Normalization**: Cleans text by removing HTML tags, scripts, and other formatting artifacts.
    *   **Whitespace & Encoding Cleanup**: Ensures consistent text formatting and handles encoding issues.
    *   **Semantic Chunking**: Divides documents into semantically coherent segments with configurable overlap for context preservation.
    *   **Metadata Management**: Attaches and preserves crucial metadata for each chunk, including parent document ID, chunk index, and position.

*   **High-Quality Embedding Generation**:
    *   Converts text chunks and queries into dense vector representations.
    *   Supports **single chunk, batch, and query embedding** operations for flexible use cases.
    *   Integrates with the **NVIDIA NIM `llama-3.2-nv-embedqa-1b-v2` model** for robust embeddings.

*   **Persistent Vector Storage and Retrieval**:
    *   Utilizes **ChromaDB** for efficient storage and retrieval of vector embeddings.
    *   Ensures **persistent disk storage** for the vector database, maintaining data integrity across sessions.

*   **Operational Logging**:
    *   Records **operational events** across all system modules.
    *   Logs cover ingestion operations, retrieval queries, model inference calls, system errors, and performance metrics to aid debugging and monitoring.

---

## Architecture & Technologies

## Architecture & Technologies

The system employs a microservice-oriented architecture, organized around a pipeline-oriented methodology for both content indexing and query processing. Each service operates independently, communicating over REST APIs and structured data interfaces, which simplifies modular development, allows independent scaling, and enhances overall system scalability and maintainability. The entire system is packaged within Docker containers for consistent runtime environments across development and deployment, leveraging environment-driven configuration for portability.

### High-Level Components

The architecture is composed of distinct processing layers orchestrated by an API Gateway:

*   **User Interface Layer**: A client interface, potentially implemented with Streamlit, for user interaction, data source uploads, query submission, and response display.
*   **API Management Layer**: Built with FastAPI, this layer serves as the backend API, providing endpoints for document/audio ingestion, webpage indexing, knowledge base querying, and document summarization. It orchestrates the execution of internal pipeline modules.
*   **Data Ingestion Layer**: Handles the conversion of various content types (files, audio, URLs) into text, assigning metadata such as `doc_id`, `source_type`, and filename. Deepgram API is utilized for speech-to-text transcription.
*   **Preprocessing and Normalization Layer**: Cleanses extracted text, removes formatting artifacts, and segments content into overlapping sentence-based chunks.
*   **Embedding Generation Module**: Generates dense vector representations for text chunks and queries using a dedicated embedding model, interfacing with external NVIDIA NIM APIs.
*   **Vector Storage Layer**: Stores embedding vectors, chunk texts, and associated metadata. It supports ChromaDB or FAISS for dense vector storage and similarity search.
*   **Query Processing Module & Retrieval Engine**: Manages user queries, normalizes and embeds them, and retrieves candidate chunks through vector similarity search. This layer also incorporates a temporal filtering subsystem for time-based metadata searches.
*   **Neural Reranking Module**: Reranks retrieved candidate chunks using a specialized neural reranking model to improve relevance, also leveraging external NVIDIA NIM APIs.
*   **Context Construction Module**: Assembles the reranked chunks into a bounded context window for the generation model.
*   **LLM Response Generation Module**: Synthesizes grounded answers, summaries, or other text outputs based on the provided context, utilizing a generation model via NVIDIA NIM APIs.
*   **Logging and Monitoring Module**: Records operational events, model inference calls, system errors, and performance metrics across all system modules for reliability and optimization.

### Key Technologies and Frameworks

*   **Backend Framework**: FastAPI for robust API management and service orchestration.
*   **Containerization**: Docker for packaging and deployment, ensuring consistent environments.
*   **User Interface**: Streamlit (as a potential client interface).
*   **Vector Databases**: ChromaDB or FAISS for efficient dense vector storage and similarity search.
*   **Embedding Model**: `llama-3.2-nemoretriever-300m-embed-v1` (accessed via NVIDIA NIM).
*   **Reranking Model**: `rerank-qa-mistral-4b` (accessed via NVIDIA NIM).
*   **Generation Model**: `qwen2-7b-instruct` (accessed via NVIDIA NIM).
*   **Speech-to-Text**: Configurable Automatic Speech Recognition (ASR) interface, with Deepgram API as an external integration.
*   **External APIs**: NVIDIA NIM APIs for advanced AI model inference (embeddings, reranking, generation) and Deepgram API for speech transcription.

### Methodology Highlights

The system operates through distinct indexing and querying phases. During **indexing**, content undergoes parsing, text extraction, normalization, chunking, embedding, and storage in the vector database. For **querying**, user questions are embedded, candidate chunks are retrieved via vector similarity, reranked, and then used to synthesize answers by a generation model. Specialized workflows include hierarchical document summarization and temporal querying, which integrates metadata filters directly into the vector database.

---

## Getting Started

### Getting Started

This project is structured as a collection of independent microservices (e.g., Preprocessing Service, Vector Store Service, Ingestion Service, Retrieval Service). Each service can be run directly using Python and Uvicorn, or deployed using Docker containers.

#### Prerequisites

*   **Python 3.x**: Ensure you have a compatible Python version installed.
*   **Uvicorn and FastAPI**: To run services directly, you will need `uvicorn` and `fastapi`. These can typically be installed via pip:
    ```bash
    pip install "uvicorn[standard]" fastapi
    ```
*   **Docker**: To build and run services as containers, Docker must be installed on your system.

#### Running Services Directly

Each microservice's entry point is an `app/main.py` file. This file contains the FastAPI application instance (`app`) and includes a block to start the Uvicorn server when executed directly.

To start a service, navigate to its root directory (where its `app` directory resides) and run:

```bash
python app/main.py
```

This will launch the FastAPI application using Uvicorn, listening on the host and port specified in the service's configuration (e.g., `settings.HOST`, `settings.PORT`), with hot-reloading enabled for development.

For example, to start the Preprocessing Service (assuming you are in its root directory):

```bash
python app/main.py
```

Once running, you can typically access the service's health check endpoint at `/health` (e.g., `http://localhost:8000/health`).

#### Running Services with Docker

The entire system is designed for containerization using Docker, ensuring consistent runtime environments across development and deployment platforms. Each service is packaged within its own Docker container, and its `Dockerfile` defines the build instructions.

To build and run a service using Docker:

1.  **Build the Docker image**: Navigate to the root directory of the specific service (the directory containing its `Dockerfile` and `app` directory).
    ```bash
    cd <service-directory> # e.g., cd ingestion-service/
    docker build -t <service-name> .
    ```
    Replace `<service-name>` with a suitable name for the image (e.g., `ingestion-service`).

2.  **Run the Docker container**: The container exposes the API service on a designated network port.
    ```bash
    docker run -p <HOST_PORT>:<CONTAINER_PORT> <service-name>
    ```
    -   Replace `<HOST_PORT>` with the port on your host machine you want to expose.
    -   Replace `<CONTAINER_PORT>` with the port the service listens on *inside* the container (typically defined in the service's settings or `Dockerfile`).

---

