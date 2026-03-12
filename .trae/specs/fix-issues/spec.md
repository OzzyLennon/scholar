# Bug Fixes and Improvements Spec

## Why
The user reported three issues:
1. `main.py` runs with a hardcoded question bank instead of accepting user input.
2. The Retrieval Agent fails to return data from real engines (likely due to strict language routing and missing keys).
3. The Streamlit UI shows "Unable to read configuration" due to a property mismatch.

## What Changes
- **Modified `main.py`**:
  - Remove the hardcoded `test_idea` execution.
  - Add logic to accept user input via command line or interactive prompt.
- **Modified `ui/components.py`**:
  - Update `render_sidebar` to use `config.agent_routes` instead of the non-existent `config.AGENT_LLMS`.
- **Modified `agents/core.py`**:
  - Adjust `SearcherAgent.search` logic: If Metaso (Chinese engine) is not available, fallback to using the Universal Search Engine (Arxiv/IEEE/SS) for Chinese queries instead of dropping them.

## Impact
- **Affected specs**: None (Bug fix).
- **Affected code**: `main.py`, `ui/components.py`, `agents/core.py`.

## MODIFIED Requirements
### Requirement: User Input in CLI
The `main.py` script SHALL prompt the user for a research topic if one is not provided, instead of running a hardcoded example immediately.

### Requirement: Robust Search Routing
The `SearcherAgent` SHALL attempt to use available search engines (Arxiv, Semantic Scholar, etc.) for all queries if the specialized language engine (Metaso) is unavailable, rather than failing silently or returning Mock data immediately for Chinese queries.

### Requirement: Correct UI Config Display
The Streamlit sidebar SHALL correctly display the Agent LLM routing configuration by accessing the correct attribute `config.agent_routes`.
