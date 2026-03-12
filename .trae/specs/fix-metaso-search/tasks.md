# Tasks

- [x] Task 1: Expose Metaso Tools
  - [x] Modify `tools/__init__.py` to import `MetasoMCPClient` and `ChinesePaper` from `.metaso_search`.
  - [x] Add them to `__all__`.

- [x] Task 2: Integrate Metaso Client in SearcherAgent
  - [x] Modify `agents/core.py`:
    - [x] Import `MetasoMCPClient` from `tools`.
    - [x] In `__init__`, replace `OpenAI` client initialization for Metaso with `MetasoMCPClient`.
    - [x] In `_search_metaso`, call `self.metaso_client.search_papers(query, limit)`.
    - [x] Convert `ChinesePaper` objects to dictionaries using `.to_dict()`.

- [x] Task 3: Verification
  - [x] Create a test script `test_metaso.py` to verify the client works with a real key (or mock if no key).
  - [x] Since we might not have a key, we should ensure the code handles missing keys gracefully (logs a warning and returns empty list/mock).
