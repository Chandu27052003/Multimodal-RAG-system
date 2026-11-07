# Preprocessing API tests

From the repository root, install the service and test dependencies, then run:

```sh
python -m pip install -r services/preprocessing/requirements-test.txt
python -m unittest discover -s services/preprocessing/tests -v
```

These tests exercise the FastAPI route, normalization, chunk assembly, and
metadata output in process. Sentence boundaries are supplied by a mock, and
the import-time NLTK download is disabled. No tokenizer data download, API key,
running service, or external model call is needed. They do not test NLTK's
sentence detection or the full ingestion/embedding/retrieval pipeline.

`POST /preprocess/` accepts an optional positive `chunk_size` and a nonnegative
`chunk_overlap`, both measured in words. Omitting an option uses its configured
default; `chunk_overlap=0` explicitly disables overlap. Invalid query values
return HTTP 422 before preprocessing starts.
