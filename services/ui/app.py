import os

import requests
import streamlit as st

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:8000")

# ── Page config ────────────────────────────────────────────────────

st.set_page_config(
    page_title="Multimodal RAG",
    page_icon="🔍",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.2rem; }
    .sub-header  { font-size: 1rem; color: #888; margin-bottom: 1.5rem; }
    .source-box  {
        border-left: 3px solid #4a90d9;
        padding: 0.8rem 1rem; margin: 0.5rem 0; border-radius: 4px;
        font-size: 0.88rem;
        color: inherit;
        background: rgba(74, 144, 217, 0.08);
    }
    .source-box b { color: inherit; }
    .score-badge {
        background: rgba(74, 144, 217, 0.18); color: #5ba0e8; padding: 2px 8px;
        border-radius: 12px; font-size: 0.78rem; font-weight: 600;
    }
    .type-badge {
        background: rgba(100, 200, 120, 0.18); color: #4caf50; padding: 2px 8px;
        border-radius: 12px; font-size: 0.72rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers ────────────────────────────────────────────────────────

def check_gateway():
    try:
        r = requests.get(f"{GATEWAY_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def get_services_health():
    try:
        r = requests.get(f"{GATEWAY_URL}/health/services", timeout=5)
        return r.json()
    except Exception:
        return None


_SOURCE_TAGS = {
    "audio": "Audio",
    "youtube": "YouTube",
    "url": "URL",
    "pdf": "PDF",
    "docx": "DOCX",
    "txt": "TXT",
    "html": "HTML",
}


def _build_source_label(meta: dict, chunk_id: str, source_type: str) -> tuple[str, str]:
    """Return (display_label, type_tag) for a source chunk."""
    tag = _SOURCE_TAGS.get(source_type, source_type.upper() if source_type else "DOC")

    if source_type == "url":
        label = meta.get("url") or meta.get("doc_id") or chunk_id
    elif source_type == "audio":
        label = meta.get("filename") or meta.get("doc_id") or chunk_id
    else:
        label = meta.get("filename") or meta.get("doc_id") or chunk_id

    return label, tag


def get_collections() -> list[str]:
    """Fetch available collection names from the gateway."""
    try:
        r = requests.get(f"{GATEWAY_URL}/api/knowledge-base/collections", timeout=5)
        if r.status_code == 200:
            return [c["name"] for c in r.json()]
    except Exception:
        pass
    return ["default"]


# ── Sidebar ────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Settings")
    available_collections = get_collections()
    if "default" not in available_collections:
        available_collections.insert(0, "default")
    collection_name = st.selectbox("Collection", options=available_collections, index=0)
    top_k = st.slider("Top-K results", min_value=1, max_value=10, value=5)

    st.markdown("---")
    st.markdown("### System Status")
    if check_gateway():
        st.success("Gateway: Connected")
        health = get_services_health()
        if health:
            for svc in health["services"]:
                if svc["status"] == "healthy":
                    st.markdown(f"&nbsp;&nbsp; :green[●] {svc['service']}")
                else:
                    st.markdown(f"&nbsp;&nbsp; :red[●] {svc['service']}")
    else:
        st.error("Gateway: Unreachable")
        st.caption("Start all services first.")


# ── Main content ───────────────────────────────────────────────────

st.markdown('<div class="main-header">Multimodal RAG System</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Upload documents, build a knowledge base, and ask questions</div>',
    unsafe_allow_html=True,
)

tab_query, tab_upload, tab_audio, tab_kb = st.tabs(
    ["Ask a Question", "Upload Documents", "Upload Audio", "Knowledge Base"]
)


# ── Tab 1: Query ───────────────────────────────────────────────────

with tab_query:
    query = st.text_area(
        "Enter your question",
        placeholder="e.g. What models are used in the system?",
        height=100,
    )

    if st.button("Search & Generate", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a question.")
        elif not check_gateway():
            st.error("Gateway is not reachable. Please start all services.")
        else:
            with st.spinner("Retrieving and generating answer..."):
                try:
                    r = requests.post(
                        f"{GATEWAY_URL}/api/query",
                        json={
                            "query": query,
                            "collection_name": collection_name,
                            "top_k": top_k,
                        },
                        timeout=120,
                    )
                    if r.status_code != 200:
                        st.error(f"Error: {r.json().get('detail', r.text)}")
                    else:
                        data = r.json()

                        st.markdown("### Answer")
                        st.markdown(data["answer"])

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Model", data.get("model", "N/A"))
                        with col2:
                            st.metric("Context tokens", f"~{data.get('context_token_estimate', 0)}")
                        with col3:
                            usage = data.get("usage") or {}
                            st.metric("Total tokens", usage.get("total_tokens", "N/A"))

                        if data.get("sources"):
                            st.markdown("### Sources")
                            for src in data["sources"]:
                                score = src.get("rerank_score")
                                score_str = f"{score:.2f}" if score is not None else "N/A"
                                meta = src.get("metadata") or {}
                                source_type = meta.get("source_type", "")
                                label, tag = _build_source_label(meta, src["chunk_id"], source_type)

                                st.markdown(
                                    f'<div class="source-box">'
                                    f'<span class="score-badge">score: {score_str}</span> '
                                    f'<span class="type-badge">{tag}</span> '
                                    f"&nbsp; <b>{label}</b><br/>"
                                    f"{src['text'][:300]}{'...' if len(src['text']) > 300 else ''}"
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the gateway. Are all services running?")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")


# ── Tab 2: Upload ──────────────────────────────────────────────────

with tab_upload:
    st.markdown("#### Upload a document to the knowledge base")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["pdf", "docx", "txt", "html"],
        help="Supported: PDF, DOCX, TXT, HTML",
    )

    upload_collection = st.text_input(
        "Target collection (type a new name to create one)",
        value=collection_name,
        key="upload_collection",
    )

    if st.button("Upload & Index", type="primary", use_container_width=True):
        if not uploaded_file:
            st.warning("Please select a file first.")
        elif not check_gateway():
            st.error("Gateway is not reachable. Please start all services.")
        else:
            with st.spinner(f"Ingesting {uploaded_file.name}..."):
                try:
                    r = requests.post(
                        f"{GATEWAY_URL}/api/ingest/file",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                        data={"collection_name": upload_collection},
                        timeout=180,
                    )
                    if r.status_code != 200:
                        st.error(f"Error: {r.json().get('detail', r.text)}")
                    else:
                        data = r.json()
                        st.success(data["message"])
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Doc ID", data["doc_id"])
                        with col2:
                            st.metric("Source type", data["source_type"])
                        with col3:
                            st.metric("Chunks indexed", data["total_chunks"])
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the gateway.")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

    st.markdown("---")
    st.markdown("#### Index a URL")
    url_input = st.text_input("Webpage URL", placeholder="https://example.com/article")

    url_collection = st.text_input(
        "Target collection (type a new name to create one)",
        value=collection_name,
        key="url_collection",
    )

    if st.button("Fetch & Index URL", use_container_width=True):
        if not url_input.strip():
            st.warning("Please enter a URL.")
        elif not check_gateway():
            st.error("Gateway is not reachable. Please start all services.")
        else:
            with st.spinner(f"Fetching {url_input}..."):
                try:
                    r = requests.post(
                        f"{GATEWAY_URL}/api/ingest/url",
                        json={"url": url_input, "collection_name": url_collection},
                        timeout=180,
                    )
                    if r.status_code != 200:
                        st.error(f"Error: {r.json().get('detail', r.text)}")
                    else:
                        data = r.json()
                        st.success(data["message"])
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Doc ID", data["doc_id"])
                        with col2:
                            st.metric("Chunks indexed", data["total_chunks"])
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the gateway.")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")


# ── Tab 3: Audio Upload ───────────────────────────────────────────

with tab_audio:
    st.markdown("#### Transcribe & Index Audio")
    st.caption(
        "Upload an audio file — it will be transcribed using Deepgram, "
        "then chunked, embedded, and stored in the knowledge base."
    )

    audio_file = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "m4a", "ogg", "flac", "webm"],
        help="Supported: WAV, MP3, M4A, OGG, FLAC, WEBM",
    )

    audio_collection = st.text_input(
        "Target collection (type a new name to create one)",
        value=collection_name,
        key="audio_collection",
    )

    if audio_file:
        st.audio(audio_file, format=f"audio/{audio_file.name.rsplit('.', 1)[-1]}")

    if st.button("Transcribe & Index", type="primary", use_container_width=True):
        if not audio_file:
            st.warning("Please select an audio file first.")
        elif not check_gateway():
            st.error("Gateway is not reachable. Please start all services.")
        else:
            with st.spinner(f"Transcribing {audio_file.name} via Deepgram and indexing..."):
                try:
                    r = requests.post(
                        f"{GATEWAY_URL}/api/ingest/file",
                        files={"file": (audio_file.name, audio_file.getvalue())},
                        data={"collection_name": audio_collection},
                        timeout=300,
                    )
                    if r.status_code != 200:
                        st.error(f"Error: {r.json().get('detail', r.text)}")
                    else:
                        data = r.json()
                        st.success(data["message"])
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Doc ID", data["doc_id"])
                        with col2:
                            st.metric("Source type", data["source_type"])
                        with col3:
                            st.metric("Chunks indexed", data["total_chunks"])
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the gateway.")
                except Exception as e:
                    st.error(f"Audio upload error: {e}")

    st.markdown("---")
    st.markdown("#### Index a YouTube Video")
    st.caption("Paste a YouTube URL — audio will be downloaded, transcribed, and indexed.")

    yt_url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        key="yt_url",
    )

    yt_collection = st.text_input(
        "Target collection (type a new name to create one)",
        value=collection_name,
        key="yt_collection",
    )

    if st.button("Transcribe YouTube Video", type="primary", use_container_width=True):
        if not yt_url.strip():
            st.warning("Please enter a YouTube URL.")
        elif not check_gateway():
            st.error("Gateway is not reachable. Please start all services.")
        else:
            with st.spinner("Downloading audio and transcribing (this may take a minute)..."):
                try:
                    r = requests.post(
                        f"{GATEWAY_URL}/api/ingest/youtube",
                        json={"url": yt_url, "collection_name": yt_collection},
                        timeout=600,
                    )
                    if r.status_code != 200:
                        st.error(f"Error: {r.json().get('detail', r.text)}")
                    else:
                        data = r.json()
                        st.success(data["message"])
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Doc ID", data["doc_id"])
                        with col2:
                            st.metric("Source type", data["source_type"])
                        with col3:
                            st.metric("Chunks indexed", data["total_chunks"])
                        extra = data.get("extra") or {}
                        if extra.get("duration_seconds"):
                            dur = extra["duration_seconds"]
                            mins, secs = divmod(int(dur), 60)
                            st.caption(
                                f"Audio duration: {mins}m {secs}s &bull; "
                                f"Confidence: {extra.get('confidence', 'N/A')}"
                            )
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the gateway.")
                except Exception as e:
                    st.error(f"YouTube error: {e}")


# ── Tab 4: Knowledge Base ─────────────────────────────────────────

with tab_kb:
    st.markdown("#### Knowledge Base Contents")
    st.caption("Browse and manage all indexed documents.")

    if st.button("Refresh", use_container_width=True):
        st.session_state["kb_refresh"] = True

    if not check_gateway():
        st.warning("Gateway is not reachable.")
    else:
        try:
            r = requests.get(
                f"{GATEWAY_URL}/api/knowledge-base/",
                params={"collection_name": collection_name},
                timeout=15,
            )
            if r.status_code != 200:
                st.error(f"Error: {r.json().get('detail', r.text)}")
            else:
                kb_data = r.json()
                docs = kb_data.get("documents", [])
                total_docs = kb_data.get("total_documents", 0)
                total_chunks = kb_data.get("total_chunks", 0)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Documents", total_docs)
                with col2:
                    st.metric("Total chunks", total_chunks)

                if not docs:
                    st.info("No documents in this collection yet. Upload some files first!")
                else:
                    st.markdown("---")
                    for doc in docs:
                        doc_id = doc["doc_id"]
                        stype = doc.get("source_type", "unknown")
                        fname = doc.get("filename") or ""
                        url = doc.get("url") or ""
                        chunks = doc.get("chunk_count", 0)

                        tag = _SOURCE_TAGS.get(stype, stype.upper())
                        if stype == "url":
                            display_name = url or doc_id
                        elif fname:
                            display_name = fname
                        else:
                            display_name = doc_id

                        with st.container():
                            c_info, c_del = st.columns([5, 1])
                            with c_info:
                                st.markdown(
                                    f'<span class="type-badge">{tag}</span> '
                                    f"&nbsp; **{display_name}**  \n"
                                    f'<span style="font-size:0.82rem;color:#888;">'
                                    f"doc_id: {doc_id} &bull; {chunks} chunk(s)"
                                    f"</span>",
                                    unsafe_allow_html=True,
                                )
                            with c_del:
                                if st.button(
                                    "Delete",
                                    key=f"del_{doc_id}",
                                    type="secondary",
                                    use_container_width=True,
                                ):
                                    try:
                                        dr = requests.delete(
                                            f"{GATEWAY_URL}/api/knowledge-base/{doc_id}",
                                            params={"collection_name": collection_name},
                                            timeout=15,
                                        )
                                        if dr.status_code == 200:
                                            st.success(
                                                f"Deleted {dr.json().get('deleted_chunks', 0)} "
                                                f"chunk(s) for {display_name}"
                                            )
                                            st.rerun()
                                        else:
                                            st.error(dr.json().get("detail", dr.text))
                                    except Exception as exc:
                                        st.error(f"Delete failed: {exc}")
                            st.markdown(
                                '<hr style="margin:0.3rem 0;border:none;'
                                'border-top:1px solid rgba(128,128,128,0.2);">',
                                unsafe_allow_html=True,
                            )
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the gateway.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
