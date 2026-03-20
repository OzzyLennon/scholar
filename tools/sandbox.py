import sys
import io
import os
import contextlib
import traceback
import signal
import threading
import queue
import matplotlib.pyplot as plt
from dataclasses import dataclass, field

# 安全警告：此沙箱使用exec()执行任意Python代码，存在安全风险。
# 在生产环境中应考虑使用容器化方案（如Docker）或更严格的隔离。

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

        # 尝试设置资源限制（仅Unix系统有效）
        try:
            import resource
            # 限制CPU时间（秒）
            resource.setrlimit(resource.RLIMIT_CPU, (self.timeout, self.timeout))
            # 限制内存（MB）
            memory_limit_mb = 512  # 512MB
            memory_limit = memory_limit_mb * 1024 * 1024  # 转换为字节
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
        except (ImportError, ValueError, OSError):
            # Windows系统或不支持resource模块，跳过资源限制
            pass

        def save_figure(filename):
            path = os.path.join(self.output_dir, filename)
            plt.savefig(path)
            figures.append(path)
            plt.close()

        # 使用线程实现超时控制
        result_queue = queue.Queue()

        def _run_code():
            try:
                with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
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
            finally:
                result_queue.put((success, error))

        # 启动执行线程
        exec_thread = threading.Thread(target=_run_code)
        exec_thread.daemon = True  # 设置为守护线程，主线程退出时自动结束
        exec_thread.start()

        # 等待线程完成或超时
        exec_thread.join(timeout=self.timeout)

        if exec_thread.is_alive():
            # 线程仍在运行，表示超时
            success = False
            error = f"Execution timeout after {self.timeout} seconds"
            # 无法安全终止线程，但daemon=True会在主线程退出时结束
        else:
            # 线程正常结束，获取结果
            try:
                success, error = result_queue.get(timeout=1)
            except queue.Empty:
                success = False
                error = "Failed to get execution result"

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
