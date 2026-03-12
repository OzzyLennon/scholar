# Tasks

- [x] Task 1: Create `tools/sandbox.py`
  - [x] Define `ExecutionResult` dataclass.
  - [x] Implement `PythonSandbox` class.
    - [x] `__init__`: Setup output directory.
    - [x] `execute`: Capture stdout/stderr, inject `save_figure`, run `exec()`.
  - [x] Define `DataAnalyzer` class (minimal implementation).

- [x] Task 2: Fix Environment
  - [x] Downgrade `numpy` to `<2` to resolve `ImportError` with `matplotlib`.

- [x] Task 3: Verify Data Analyst Agent
  - [x] Create a test script `test_sandbox.py` that uses `PythonSandbox` to run a script that plots a chart.
  - [x] Verify that the chart is saved to `output/`.
  - [x] Verify that `stdout` is captured.

- [x] Task 4: Integration Check
  - [x] Ensure `tools/__init__.py` imports `PythonSandbox` correctly.
