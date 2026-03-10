# ==========================================
# 工具层 - Python 沙箱执行
# ==========================================
import os
import json
import tempfile
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExecutionResult:
    """代码执行结果"""
    success: bool
    output: str
    error: str = ""
    figures: List[str] = None
    dataframes: Dict[str, Any] = None
    execution_time: float = 0.0
    
    def __post_init__(self):
        if self.figures is None:
            self.figures = []
        if self.dataframes is None:
            self.dataframes = {}


class PythonSandbox:
    """
    Python 沙箱执行环境
    
    功能：
    1. 安全执行 Python 代码
    2. 自动捕获 matplotlib 图表
    3. 支持常见数据分析库
    """
    
    def __init__(self, timeout: int = 60, max_output_size: int = 10000, output_dir: str = None):
        self.timeout = timeout
        self.max_output_size = max_output_size
        self.output_dir = output_dir or os.getenv("OUTPUT_DIR", "./output")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def execute(self, code: str, context: Dict = None) -> ExecutionResult:
        """
        执行 Python 代码
        
        Args:
            code: Python 代码字符串
            context: 执行上下文（可选的预定义变量）
        
        Returns:
            ExecutionResult
        """
        start_time = datetime.now()
        
        # 准备执行脚本
        wrapper_code = self._wrap_code(code, context or {})
        
        # 写入临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(wrapper_code)
            temp_file = f.name
        
        try:
            # 执行代码（不改变工作目录，避免创建子目录）
            result = subprocess.run(
                ['python3', temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # 解析输出
            output = result.stdout[:self.max_output_size]
            error = result.stderr[:self.max_output_size] if result.returncode != 0 else ""
            
            # 收集生成的图表
            figures = self._collect_figures()
            
            # 收集数据（如果有的话）
            dataframes = self._extract_dataframes()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ExecutionResult(
                success=result.returncode == 0,
                output=output,
                error=error,
                figures=figures,
                dataframes=dataframes,
                execution_time=execution_time
            )
        
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error=f"执行超时（超过 {self.timeout} 秒）"
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e)
            )
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def _wrap_code(self, code: str, context: Dict) -> str:
        """包装代码，添加必要的导入和配置"""
        
        # 构建包装代码
        # 使用传入的 output_dir，避免目录嵌套
        safe_output_dir = self.output_dir.replace("\\", "/")
        imports = f'''
import os
import sys
import json
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from io import StringIO

# 配置 matplotlib
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = 100

# 输出目录（使用绝对路径避免嵌套）
OUTPUT_DIR = "{safe_output_dir}"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 计数器（用于自动命名图表）
_fig_cnt = [0]

def save_figure(name=None):
    """保存当前图表"""
    _fig_cnt[0] += 1
    if name is None:
        name = "figure_" + str(_fig_cnt[0])
    path = os.path.join(OUTPUT_DIR, name + ".png")
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print("[Figure saved: " + path + "]")
    return path
'''
        
        footer = '''

# 自动保存未关闭的图表
if plt.get_fignums():
    for i, fig_num in enumerate(plt.get_fignums()):
        plt.figure(fig_num)
        save_figure("auto_figure_" + str(i+1))

print("[Execution completed successfully]")
'''
        
        wrapper = imports + "\n# 用户代码开始\n# =============\n\n" + code + "\n# =============\n# 用户代码结束\n" + footer
        
        return wrapper
    
    def _collect_figures(self) -> List[str]:
        """收集生成的图表文件（包括嵌套的output目录）"""
        figures = []
        # 检查主输出目录
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                fpath = os.path.join(self.output_dir, f)
                if f.endswith('.png') and os.path.getmtime(fpath) > datetime.now().timestamp() - 300:
                    figures.append(fpath)
        
        # 检查嵌套的 output/output 目录
        nested_output = os.path.join(self.output_dir, 'output')
        if os.path.exists(nested_output):
            for f in os.listdir(nested_output):
                fpath = os.path.join(nested_output, f)
                if f.endswith('.png') and os.path.getmtime(fpath) > datetime.now().timestamp() - 300:
                    figures.append(fpath)
        
        return figures
    
    def _extract_dataframes(self) -> Dict[str, Any]:
        """提取生成的数据（如果有的话）"""
        # 这里可以扩展，读取保存的 CSV 或 JSON 文件
        return {}


class DataAnalyzer:
    """
    数据研究员的完整数据分析能力
    整合代码生成、执行、结果解析
    """
    
    def __init__(self, llm_client=None, sandbox_timeout: int = 120):
        self.llm_client = llm_client
        # 使用配置中的输出目录，避免嵌套
        output_dir = os.getenv("OUTPUT_DIR", "./output")
        self.sandbox = PythonSandbox(timeout=sandbox_timeout, output_dir=output_dir)
        self.analysis_history = []
    
    def analyze(self, requirement: str, context: Dict = None) -> Dict:
        """
        执行数据分析任务
        
        Args:
            requirement: 分析需求描述
            context: 额外上下文（如文献数据）
        
        Returns:
            分析结果字典
        """
        print(f"\n[📊 数据研究员] 分析需求: {requirement}")
        
        # 1. 生成代码（如果需要 LLM）
        if self.llm_client:
            code = self._generate_code(requirement, context)
        else:
            code = self._get_mock_code(requirement)
        
        print(f"[📊 数据研究员] 生成代码:\n{code[:200]}...\n")
        
        # 2. 执行代码
        result = self.sandbox.execute(code, context)
        
        # 3. 解析结果
        if result.success:
            analysis = {
                "status": "success",
                "output": result.output,
                "figures": result.figures,
                "execution_time": result.execution_time,
                "insights": self._extract_insights(result.output)
            }
        else:
            analysis = {
                "status": "error",
                "error": result.error,
                "output": result.output
            }
        
        self.analysis_history.append(analysis)
        return analysis
    
    def _generate_code(self, requirement: str, context: Dict = None) -> str:
        """使用 LLM 真实生成数据分析代码"""
        if not self.llm_client:
            print("[⚠️ 数据研究员] 未配置 LLM 客户端，使用 Mock 代码")
            return self._get_mock_code(requirement)
            
        print("[📊 数据研究员] 正在思考并编写 Python 代码...")
        
        # 将前置文献审查的发现作为上下文喂给写代码的模型
        context_str = ""
        if context and 'research_gaps' in context:
            gaps = json.dumps(context['research_gaps'], ensure_ascii=False)
            context_str = f"当前研究空白背景：{gaps}\n请在代码分析中尽可能回应这些背景。"

        try:
            # 这里的 system prompt 可以引入 prompts 模块里的 DATA_RESEARCHER_CODE_GENERATION_PROMPT
            from prompts.system_prompts import DATA_RESEARCHER_CODE_GENERATION_PROMPT
            
            response = self.llm_client.chat.completions.create(
                model=os.getenv("MODEL_NAME", "deepseek-chat"), # 这里会自动使用传入的 client 的对应模型
                temperature=0.1, # 编写代码的温度要尽可能的低，保持严谨
                messages=[
                    {"role": "system", "content": DATA_RESEARCHER_CODE_GENERATION_PROMPT},
                    {"role": "user", "content": f"{context_str}\n\n我的具体数据分析需求是：{requirement}\n\n请直接输出 Python 代码，不要有任何额外的文字解释。"}
                ]
            )
            
            code = response.choices[0].message.content.strip()
            
            # 🛡️ 清洗防御：去除大模型经常带上的 Markdown 代码块标记
            if code.startswith("```python"):
                code = code[9:]
            elif code.startswith("```"):
                code = code[3:]
            
            if code.endswith("```"):
                code = code[:-3]
                
            return code.strip()
            
        except Exception as e:
            print(f"[⚠️ 数据研究员] 代码生成失败: {e}，回退到 Mock 代码")
            return self._get_mock_code(requirement)
    
    def _get_mock_code(self, requirement: str) -> str:
        """Mock 代码示例"""
        return '''
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 生成模拟数据
np.random.seed(42)
n_samples = 100

traditional_times = np.random.normal(60, 15, n_samples)  # 传统方法用时（分钟）
automated_times = np.random.normal(35, 10, n_samples)    # 自动化方法用时（分钟）

# 创建 DataFrame
df = pd.DataFrame({
    'traditional': traditional_times,
    'automated': automated_times
})

# 统计分析
print("=== 效率对比分析 ===")
print(f"传统方法平均用时: {traditional_times.mean():.2f} 分钟")
print(f"自动化方法平均用时: {automated_times.mean():.2f} 分钟")
print(f"效率提升: {(1 - automated_times.mean()/traditional_times.mean())*100:.1f}%")

# 统计检验
from scipy import stats
t_stat, p_value = stats.ttest_ind(traditional_times, automated_times)
print(f"\\nt检验: t={t_stat:.2f}, p={p_value:.4f}")

if p_value < 0.05:
    print("结论: 两种方法存在显著差异 (p < 0.05)")
else:
    print("结论: 两种方法无显著差异")

# 可视化对比
plt.figure(figsize=(12, 5))

# 子图1: 箱线图
plt.subplot(1, 2, 1)
plt.boxplot([traditional_times, automated_times], labels=['传统方法', '自动化方法'])
plt.ylabel('用时 (分钟)')
plt.title('文献收集效率对比')
plt.grid(True, alpha=0.3)

# 子图2: 柱状图
plt.subplot(1, 2, 2)
methods = ['传统方法', '自动化方法']
times = [traditional_times.mean(), automated_times.mean()]
colors = ['#ff7f7f', '#7fbf7f']
plt.bar(methods, times, color=colors, alpha=0.7)
plt.ylabel('平均用时 (分钟)')
plt.title('效率提升对比')
plt.grid(True, alpha=0.3, axis='y')

for i, v in enumerate(times):
    plt.text(i, v + 1, f'{v:.1f}分钟', ha='center', fontweight='bold')

plt.tight_layout()
save_figure('efficiency_comparison')

# 相关性分析（模拟）
print("\\n=== 额外分析 ===")
correlation = np.corrcoef(traditional_times, automated_times)[0, 1]
print(f"两种方法的相关系数: {correlation:.3f}")
'''
    
    def _extract_insights(self, output: str) -> List[str]:
        """从输出中提取关键洞察"""
        insights = []
        for line in output.split('\n'):
            if any(kw in line for kw in ['效率提升', '结论', '相关系数', '显著']):
                insights.append(line.strip())
        return insights[:5]
    
    def get_analysis_report(self) -> str:
        """生成分析报告"""
        if not self.analysis_history:
            return "暂无分析记录"
        
        latest = self.analysis_history[-1]
        
        report = f"""
## 数据分析报告

**执行状态**: {latest.get('status', 'unknown')}
**执行时间**: {latest.get('execution_time', 0):.2f} 秒
**生成图表**: {len(latest.get('figures', []))} 张

### 输出摘要
```
{latest.get('output', '')[:500]}
```

### 关键洞察
"""
        for insight in latest.get('insights', []):
            report += f"- {insight}\n"
        
        return report
