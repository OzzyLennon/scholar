# Tasks

- [x] Task 1: Fix Streamlit UI Config Error
  - [x] Update `ui/components.py` to replace `config.AGENT_LLMS` with `config.agent_routes`.
  - [x] Verify that the sidebar renders without the "Unable to read configuration" warning.

- [x] Task 2: Improve Search Agent Routing
  - [x] Modify `agents/core.py` in `SearcherAgent.search` method.
  - [x] Implement fallback logic: If `self.use_metaso` is False, append `zh_queries` to `en_queries` (or process them with `self.search_engine`) to ensure they are attempted against other engines.

- [x] Task 3: Enable User Input in `main.py`
  - [x] Modify `main.py` to remove the auto-execution of the hardcoded `test_idea`.
  - [x] Add `input()` prompt to ask the user for a research topic.
  - [x] Retain the hardcoded idea as an optional default/example if the user inputs nothing.
