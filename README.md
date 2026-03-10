# Scholar - 5-Agent 学术工作流引擎

🤖 **自动化学术论文生成系统** - 5个智能Agent协同工作，从文献检索到论文生成全流程自动化

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    🧠 主控 Agent (Lead Author)              │
│                  破题规划 + 路径决策 + 最终统稿               │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┐
        ▼             ▼             ▼             ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ 🔍 检索员 │  │ 📦 提取员 │  │ 📖 审查员 │  │ 📊 数据   │
   │ Searcher │  │Extractor │  │Reviewer │  │Researcher│
   │         │  │         │  │         │  │         │
   │ 文献搜索 │  │ 数据清洗 │  │ RAG检索 │  │ Python   │
   │ 英文+中文│  │ 向量存储 │  │ Gap分析 │  │ 代码生成 │
   └─────────┘  └─────────┘  └─────────┘  └─────────┘
```

## 核心特性

- ✅ **5-Agent 架构**：主控、检索员、提取员、审查员、数据研究员协同工作
- ✅ **多 LLM 支持**：不同 Agent 可配置不同 LLM（DeepSeek-R1、豆包代码等）
- ✅ **双源检索**：Semantic Scholar（英文）+ 秘塔MCP（中文）
- ✅ **向量存储**：ChromaDB 向量库 + Zotero 书目管理
- ✅ **动态激活**：数据研究员仅在需要时唤醒
- ✅ **研究空白分析**：自动识别文献中的研究空白

## 快速开始

### 1. 安装依赖

```bash
cd scholar
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key
```

### 3. 运行

```python
from workflow import FiveAgentWorkflow

workflow = FiveAgentWorkflow()
project = workflow.run("你的研究课题")
```

### 4. 查看输出

论文和日志保存在 `./output/` 目录：
- `proj_YYYYMMDD_HHMMSS.md` - 生成的论文
- `proj_YYYYMMDD_HHMMSS.json` - 执行日志

## Agent 功能说明

| Agent | 职责 | 推荐LLM |
|-------|------|---------|
| 🧠 主控 (Lead Author) | 破题规划、路径决策、统稿 | DeepSeek-R1 |
| 🔍 检索员 (Searcher) | 文献检索（英文+中文） | - |
| 📦 提取员 (Extractor) | 数据清洗、向量存储 | - |
| 📖 审查员 (Reviewer) | RAG检索、研究空白分析 | DeepSeek-R1 |
| 📊 数据研究员 (Data) | Python代码生成、数据分析 | 豆包代码 |

## 项目结构

```
scholar/
├── agents/
│   ├── core.py          # 5个Agent核心实现
│   └── __init__.py
├── prompts/
│   ├── system_prompts.py # Agent系统提示词
│   └── __init__.py
├── tools/
│   ├── literature_search.py  # Semantic Scholar API
│   ├── metaso_search.py      # 秘塔MCP中文检索
│   └── vector_store.py       # 向量存储
├── workflow.py          # 工作流引擎
├── config.py            # 配置管理
├── main.py              # 主入口
├── requirements.txt
├── .env.example         # 环境变量模板
└── README.md
```

## 配置说明

### 多 LLM 配置

在 `config.py` 中配置不同 Agent 使用的 LLM：

```python
AGENT_LLMS = {
    "lead_author": {
        "provider": "deepseek",
        "model": "deepseek-reasoner",  # 强推理
        "temperature": 0.7
    },
    "reviewer": {
        "provider": "deepseek",
        "model": "deepseek-reasoner",
        "temperature": 0.5
    },
    "data_researcher": {
        "provider": "tencent",
        "model": "doubao-seed-2.0-code",  # 代码生成
        "temperature": 0.3
    }
}
```

## 示例输出

生成论文示例：

```markdown
# 从巴别塔到"终极翻译者"：论大型语言模型对翻译实践及语言权力结构的冲击

## 摘要
本文从语言哲学与社会批判理论视角...

## 第一章：理论基础
### 1.1 翻译：在可译与不可译之间
...

## 参考文献
[1] Benjamin, W. "The Task of the Translator"...
```

## 注意事项

1. **API Key 安全**：请勿将 `.env` 文件提交到 Git
2. **Semantic Scholar 限流**：如遇 429 错误，系统会自动降级到秘塔MCP
3. **LLM 选择**：推理任务推荐 DeepSeek-R1，代码生成推荐豆包代码

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
