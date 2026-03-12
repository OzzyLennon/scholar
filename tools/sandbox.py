import sys
import io
import os
import contextlib
import traceback
import matplotlib.pyplot as plt
from dataclasses import dataclass, field

@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str
    figures: list = field(default_factory=list)

class PythonSandbox:
    def __init__(self, timeout=120, output_dir="./output"):
        self.timeout = timeout
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def execute(self, code: str) -> ExecutionResult:
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        figures = []

        def save_figure(filename):
            path = os.path.join(self.output_dir, filename)
            plt.savefig(path)
            figures.append(path)
            plt.close()

        # Context manager to redirect stdout/stderr
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            try:
                # Prepare globals with injected helper
                exec_globals = {
                    "save_figure": save_figure,
                    "plt": plt, 
                }
                exec(code, exec_globals)
                success = True
                error = ""
            except Exception:
                success = False
                error = traceback.format_exc()

        output = stdout_buffer.getvalue()
        if not error:
             # Check if anything was printed to stderr (e.g. warnings)
             stderr_output = stderr_buffer.getvalue()
             if stderr_output:
                 output += "\nStderr:\n" + stderr_output
        else:
             # If exception occurred, stderr might contain relevant info too
             stderr_output = stderr_buffer.getvalue()
             if stderr_output:
                 error += "\nStderr:\n" + stderr_output

        return ExecutionResult(success=success, output=output, error=error, figures=figures)

class DataAnalyzer:
    def __init__(self, output_dir="./output"):
        self.sandbox = PythonSandbox(output_dir=output_dir)

    def execute(self, code: str) -> ExecutionResult:
        return self.sandbox.execute(code)
