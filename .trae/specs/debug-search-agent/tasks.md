# Tasks

- [x] Task 1: Create Debug Script
  - [x] Create `debug_search.py` in the root directory.
  - [x] Implement key verification (check if keys are present in `config.py`).
  - [x] Instantiate `SearcherAgent` and run `search(["Deep Learning"])`.
  - [x] Print results.

- [ ] Task 2: Enhance Logging in Literature Search Tools
  - [ ] Modify `tools/literature_search.py` to print specific error messages (e.g., status codes, response content) when requests fail.
  - [ ] Specifically check `IEEEAPI`, `CoreAPI`, `ArxivSearcher`, `SemanticScholarAPI` methods.

- [x] Task 3: Fix Import Error in `tools/__init__.py`
  - [x] Wrap `from .sandbox import ...` in `try...except ImportError` to prevent module loading failure when `sandbox.py` is missing.
  - [x] This allows `LiteratureSearchManager` to be imported even if `sandbox` is broken.

- [x] Task 4: Add Error Logging to `agents/core.py`
  - [x] Modify `SearcherAgent.__init__` to print the exception when `LiteratureSearchManager` import fails.

- [x] Task 5: Verify Fix
  - [x] Run `debug_search.py` again to confirm `SearcherAgent` initializes correctly and returns real results.
