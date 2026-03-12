# Debug Literature Search Agent Spec

## Why
The user reports that the Literature Search Agent fails to retrieve real data and falls back to Mock mode, even though API keys (IEEE, CORE, Metaso) are configured in `.env`. We need to investigate why the search engines are returning no results or failing.

## What Changes
- Create a reproduction/debug script `debug_search.py` to:
  - Load environment variables.
  - Print the status of API keys (masked) to verify they are loaded.
  - Initialize `SearcherAgent`.
  - Run a search with a simple query (e.g., "Deep Learning").
  - Print detailed logs of what each search engine returns.
- Modify `tools/literature_search.py` (temporarily or permanently) to add more debug logging if necessary, to see why specific engines fail (e.g. network error, auth error).

## Impact
- **Affected specs**: None (Debug task).
- **Affected code**: `tools/literature_search.py` (adding logs), new file `debug_search.py`.

## ADDED Requirements
### Requirement: Debug Script
A script `debug_search.py` SHALL be created to isolate and test the `SearcherAgent` and its underlying `LiteratureSearchManager`.

### Requirement: Enhanced Logging
The `LiteratureSearchManager` and individual API classes SHALL print more descriptive error messages when exceptions occur, to help diagnose network or auth issues.

## MODIFIED Requirements
None.
