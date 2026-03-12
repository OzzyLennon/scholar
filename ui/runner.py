import threading
import queue
import builtins

def run_workflow_thread(idea: str, log_q: queue.Queue):
    """在独立线程中运行工作流，通过队列回传状态"""
    try:
        # 动态 patch：把 print 重定向到队列
        _orig_print = builtins.print
        def _q_print(*args, **kwargs):
            msg = " ".join(str(a) for a in args)
            log_q.put(("log", msg))
            _orig_print(*args, **kwargs)
        builtins.print = _q_print

        from workflow import SixAgentWorkflow
        wf = SixAgentWorkflow()

        # 阶段钩子：在工作流类里直接 monkey-patch _print_header
        _orig_header = wf._print_header
        stage_map = {
            "阶段 1": "planning",
            "阶段 2": "searching",
            "阶段 3": "extracting",
            "阶段 4": "reviewing",
            "阶段 5": "data_pipeline",
            "阶段 6": "writing",
        }
        def _q_header(title: str):
            for key, sid in stage_map.items():
                if key in title:
                    log_q.put(("stage", sid))
                    break
            _orig_header(title)
        wf._print_header = _q_header

        project = wf.run(idea)
        log_q.put(("done", project))

    except Exception as e:
        import traceback
        log_q.put(("error", f"{e}\n{traceback.format_exc()}"))
    finally:
        builtins.print = _orig_print  # type: ignore
