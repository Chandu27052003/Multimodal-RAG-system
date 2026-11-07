# Open Knowledge Format: first, offline increment

## Decision

OKF is useful here as an **optional knowledge import/interchange layer**, not
as a replacement for multimodal ingestion, embeddings, Chroma, or RAG.
This branch deliberately implements only local concept parsing and request
preparation. It changes no running service or existing ingestion behavior.

Google Cloud's [introduction](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
describes a portable Markdown/YAML knowledge format. The canonical
[v0.2 specification](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md)
defines concept paths, optional provenance, verification and lifecycle fields.
The specification inspected for this increment has Git blob SHA
`c06e3eede0c910d0ecf12524c34204156f8795ac` (checked November 7, 2026).
Google's older knowledge-catalog copy is frozen; use the canonical repository.

## Why this fits this repository

On baseline commit `4c88047`, ingestion does not accept `.md`. The preprocessing
request already accepts `extra_metadata`, and its chunk builder preserves that
dictionary. However, the gateway's file pipeline retains only a few scalar
fields when storing chunks. Simply adding a Markdown parser would therefore
lose provenance before retrieval.

This adapter prepares one preprocessing request per concept, retaining its
bundle-relative ID, full Markdown body, and frontmatter. Existing preprocessing
schema/chunk-builder compatibility is tested directly. That establishes a
small reusable boundary before changing the distributed pipeline.

Potential benefits of later integration:

* Human-readable, version-controlled, portable knowledge instead of only an
  opaque vector collection.
* Provenance, source time offsets, and custom domain metadata can survive
  ingestion; no Google account or Google-specific runtime is required.
* Explicit links and lifecycle fields can support future relationship-aware
  retrieval and stale-content warnings.

These are integration opportunities, **not demonstrated answer-quality gains**.
OKF alone does not improve OCR/ASR, embeddings, reranking, or hallucination rates.
Curating correct concepts has a maintenance cost. Links and verification labels
are untrusted input, not proof of truth or permission to execute anything.

## Run locally

From the repository root, with Python 3.10 or newer:

```sh
python -m pip install -r requirements-okf.txt
python -m unittest discover -s tests -p 'test_okf.py' -v
python -m tools.prepare_okf examples/okf --bundle-id synthetic-demo > /tmp/okf-requests.jsonl
```

Each JSONL record matches the existing `PreprocessRequest` shape. The tool
only writes stdout. It does not upload documents, call services, fetch links,
run models, change collections, or execute `executor`/`attester` code.
Invalid input returns exit code 1 and no JSON output. Shell redirection can
still create/truncate its chosen output file, so use a new destination.

Keep `--bundle-id` unique and stable for each logical bundle. Document IDs are
deterministic from the namespace plus concept path, independent of content.
This is preparation only: **do not feed repeated imports to the existing
Chroma `add` path and assume updates work**. Replacement, removal of old chunks,
and ingestion transactions still need a separate integration design.

## Compatibility and safety boundaries

* Accepts minimal `type`-only concepts, unknown types/fields, missing optional
  metadata, broken links, and unrecognized bundle version declarations.
* Preserves timestamps as strings and normalizes a bare `verified` mapping to
  a one-element list, as v0.2 requires. It does not invent trust or freshness.
* Preserves the Markdown body, including tables, links, and code, as inert text.
* Skips reserved `index.md` and `log.md` files and Git's `.git` directories.
  It does **not** validate indexes/logs or claim full bundle conformance.
* Local safety profile: 1 MiB/concept, 8 MiB total concept bytes, 1000 directory
  entries, directory depth 32, YAML depth 32 and node count 10000. No symlinks, YAML aliases,
  duplicate keys, non-string mapping keys, or non-JSON values. PyYAML's safe
  scalar parsing rules apply. Some otherwise valid YAML therefore needs
  simplification before this adapter can consume it.
* Loads UTF-8 only, tolerates a UTF-8 BOM and CRLF, and fails closed on an
  unreadable/malformed concept before emitting records. Bounds are for local
  usage, not a substitute for a sandbox or authenticated upload service.
  Use a directory that is not being modified concurrently; this is not a
  hardened multi-user filesystem boundary.

## What has and has not been tested

The offline suite checks parser semantics, metadata preservation, deterministic
IDs, malformed and hostile YAML, resource limits, traversal/symlink rejection,
reserved files, Unicode, CLI exit/output behavior, and the actual preprocessing
request/chunk metadata contract. No network/model credentials are needed.

No full Docker stack, live NVIDIA/Deepgram calls, real Chroma import, retrieval
benchmark, or generated-answer comparison is part of this increment. No recall,
latency, token-cost, or answer-accuracy improvement is claimed.

## Later increments, only after this foundation is reviewed

1. Add optional API ingestion and preserve selected metadata through the gateway
   into Chroma with explicit serialization and update/deletion semantics.
2. Expose source/lifecycle information in retrieval and citations. Keep declared
   verification separate from independently checked facts.
3. Compare baseline RAG and OKF-enriched RAG on the same representative questions,
   documents, model settings and token budget. Measure evidence recall, citation
   correctness, answer faithfulness, latency and ingestion overhead before
   enabling any retrieval change by default.
