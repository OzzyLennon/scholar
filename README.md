# Scholar - 6-Agent 学术工作流引擎

🤖 **自动化学术论文生成系统** — 6 个智能 Agent 协同工作，从文献检索到论文生成全流程自动化。

## 架构设计

```
┌──────────────────────────────────────────────────────────────────┐
│                  🧠 主控 Agent (Lead Author)                      │
│             破题规划 + 质量把控 + 最终统稿                          │
└────────────────────────┬─────────────────────────────────────────┘
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
  ┌─────────┐      ┌─────────┐      ┌─────────┐
  │ 🔍 检索员 │      │ 📦 提取员 │      │ 📖 审查员 │
  │Searcher │      │Extractor│      │Reviewer │
  │ 文献搜索  │      │ 数据清洗  │      │ RAG检索  │
  │英文+中文 │      │ 向量存储  │      │ Gap分析  │
  └─────────┘      └─────────┘      └─────────┘
                                          │
                         ┌────────────────┘
                         ▼
          ┌──────────────────────────────┐
          │   📊 数据双子星流水线 (按需激活)  │
          │  🕷️ 采集员 → 📈 分析员         │
          │  DataCrawler → DataAnalyst   │
          └──────────────────────────────┘
```

## 核心特性

- ✅ **6-Agent 架构**：主控、检索员、提取员、审查员、采集员、分析员强解耦协同
- ✅ **多 LLM 支持**：不同 Agent 可配置不同平台和模型（DeepSeek-R1、Kimi-K2.5、DeepSeek-V3.2 等）
- ✅ **双源检索**：Semantic Scholar（英文）+ 秘塔MCP（中文）
- ✅ **Hybrid RAG**：ChromaDB（优先）+ 本地倒排索引（降级兜底），带权威性二次重排
- ✅ **数据双子星**：采集员负责爬虫落盘 CSV，分析员负责统计检验与可视化绘图（强解耦）
- ✅ **动态激活**：数据流水线仅在主控判定 `needs_data_analysis=true` 时才会启动
- ✅ **Mock 兜底**：无 API Key 时全系统自动回退到 Mock 模式，保证可运行

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key（至少填一个即可运行）
```

### 3. 运行

```python
from workflow import SixAgentWorkflow

workflow = SixAgentWorkflow()
project = workflow.run("你的研究课题")
```

或直接运行主入口：

```bash
python main.py
```

### 4. 查看输出

论文和日志保存在 `./output/` 目录：
- `proj_YYYYMMDD_HHMMSS.md` — 生成的 Markdown 论文
- `proj_YYYYMMDD_HHMMSS.json` — 详细的运行日志
- `scraped_data.csv` — 采集员落盘的原始数据（如有）
- `*.png` — 分析员生成的学术图表（如有）

## Agent 功能说明

| Agent | 职责 | 推荐 LLM |
|-------|------|----------|
| 🧠 主控 (Lead Author) | 破题规划、质量把控、最终统稿 | DeepSeek-R1 (官方) |
| 🔍 检索员 (Searcher) | 文献检索（英文 + 中文）、去重 | — (纯 API 调用) |
| 📦 提取员 (Extractor) | Citation Velocity 权威性加权、数据清洗、向量入库 | — (纯算法) |
| 📖 审查员 (Reviewer) | Hybrid RAG 混合检索、研究空白提炼、章节分发 | Kimi-K2.5 (SiliconFlow) |
| 🕷️ 采集员 (DataCrawler) | 动态生成爬虫代码并执行，落盘 CSV | DeepSeek-V3.2 (SiliconFlow) |
| 📈 分析员 (DataAnalyst) | 读取 CSV 进行统计检验与学术可视化 | DeepSeek-V3.2 (SiliconFlow) |

## 项目结构

```
scholar/
├── agents/
│   ├── core.py           # 6 个 Agent 核心实现
│   └── __init__.py
├── prompts/
│   ├── system_prompts.py # 所有 Agent 的系统提示词
│   └── __init__.py
├── tools/
│   ├── literature_search.py   # Semantic Scholar API 封装
│   ├── metaso_search.py       # 秘塔MCP 中文检索
│   ├── vector_store.py        # ChromaDB + 本地倒排索引双引擎
│   ├── sandbox.py             # Python 沙箱执行环境
│   └── data_analysis.py       # 数据分析工具
├── workflow.py           # SixAgentWorkflow 工作流引擎
├── config.py             # 配置管理（多平台 LLM 路由）
├── main.py               # 主入口
├── requirements.txt
├── .env.example          # 环境变量模板
└── README.md
```

## 配置说明

### 多平台 LLM 路由

各 Agent 使用哪个平台和模型通过环境变量灵活配置，默认值如下：

| 环境变量 | 默认值 | 说明 |
|---------|-------|------|
| `AGENT_LEAD_AUTHOR_PROVIDER` | `deepseek` | 主控平台 |
| `AGENT_LEAD_AUTHOR_MODEL` | `deepseek-reasoner` | 主控模型 (DeepSeek-R1) |
| `AGENT_REVIEWER_PROVIDER` | `siliconflow` | 审查员平台 |
| `AGENT_REVIEWER_MODEL` | `Pro/moonshotai/Kimi-K2.5` | 审查员模型 |
| `AGENT_CRAWLER_PROVIDER` | `siliconflow` | 采集员平台 |
| `AGENT_CRAWLER_MODEL` | `deepseek-ai/DeepSeek-V3.2` | 采集员模型 |
| `AGENT_ANALYST_PROVIDER` | `siliconflow` | 分析员平台 |
| `AGENT_ANALYST_MODEL` | `deepseek-ai/DeepSeek-V3.2` | 分析员模型 |
| `MAX_SEARCH_RESULTS` | `20` | 最大检索文献数 |
| `SANDBOX_TIMEOUT` | `120` | 沙箱超时秒数 |

支持的平台：`openai`、`deepseek`、`deepseek-reasoner`、`siliconflow`、`ark`、`tencent`、`kimi`、`glm`

### 支持的 API Keys

在 `.env` 文件中填入对应平台的 Key 即可激活：

```env
DEEPSEEK_KEY=sk-xxx          # DeepSeek 官方
SILICONFLOW_KEY=sk-xxx       # SiliconFlow（Kimi / DeepSeek-V3.2）
ARK_KEY=xxx                  # 火山方舟（Ark / Kimi / GLM）
TENCENT_KEY=xxx              # 腾讯云
OPENAI_API_KEY=sk-xxx        # OpenAI

SEMANTIC_SCHOLAR_API_KEY=xxx # Semantic Scholar（可选，无 Key 也能检索）
METASO_API_KEY=xxx           # 秘塔MCP 中文检索（可选）
```

## 工作流阶段

```
阶段 1: 🧠 主控破题规划       → 生成大纲 + 检索词 + 是否需要数据分析
阶段 2: 🔍 检索员文献搜索      → 英文(SS) + 中文(秘塔) → 去重
阶段 3: 📦 提取员权威性加权    → Citation Velocity 打分 → 向量入库
阶段 4: 📖 审查员 Hybrid RAG  → 混合检索 + Gap 提炼 + 章节分发
阶段 5: 📊 数据双子星 (按需)   → 采集员生成爬虫 → 分析员统计+绘图
阶段 6: ✍️ 主控最终统稿        → 整合素材 → 输出 Markdown 论文
```

## 示例输出

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

1. **API Key 安全**：请勿将 `.env` 文件提交到 Git（已在 `.gitignore` 中排除）
2. **Semantic Scholar 限流**：如遇 429 错误，系统会自动降级到秘塔MCP或 Mock 模式
3. **爬虫网络**：`DataCrawlerAgent` 优先使用 Jina Reader (r.jina.ai) 规避反爬，需保证外网访问
4. **ChromaDB**：若未安装，系统自动降级到本地倒排索引引擎，无需手动处理
5. **Mock 模式**：无任何 API Key 时，系统会全程使用 Mock 数据完整运行，方便本地调试

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
