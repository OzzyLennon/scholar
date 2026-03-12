# Fix Metaso Search Integration Spec

## Why
The `README.md` claims "Secret Tower MCP (Chinese)" for dual-source search. However, the current `SearcherAgent` implementation relies on prompting an OpenAI-compatible model (`metaso-search`) to generate JSON search results, which is prone to hallucinations and format errors.
Meanwhile, a robust `tools/metaso_search.py` exists (implementing a proper MCP client) but is unused and not exposed in `tools/__init__.py`.
To ensure "Real Data" and reliability, we must integrate the dedicated MCP client.

## What Changes
- **Modify `tools/__init__.py`**: Import and expose `MetasoMCPClient` and `ChinesePaper`.
- **Modify `agents/core.py`**:
  - In `SearcherAgent.__init__`, initialize `MetasoMCPClient` if `METASO_API_KEY` is present.
  - In `SearcherAgent._search_metaso`, use `self.metaso_client.search_papers(query)` instead of prompting an LLM.
  - Adapt the return type to match the expected dictionary format (using `.to_dict()`).

## Impact
- **Affected specs**: None (Fix/Optimization).
- **Affected code**: `tools/__init__.py`, `agents/core.py`.

## ADDED Requirements
### Requirement: Metaso MCP Integration
The `SearcherAgent` SHALL use the `MetasoMCPClient` to perform structured searches against the Metaso API when handling Chinese queries.

## MODIFIED Requirements
### Requirement: Search Result Format
The search results from Metaso SHALL be converted to standard dictionaries with `title`, `authors`, `year`, `abstract`, `doi`, `citations`, `source` fields to be compatible with the rest of the workflow.
