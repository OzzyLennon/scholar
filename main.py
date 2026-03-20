# ==========================================
# Scholar - 6-Agent 学术工作流引擎 (究极完全体)
# ==========================================
import sys
import io
from workflow import SixAgentWorkflow
from config import config

# 修复Windows控制台编码问题
if sys.platform == "win32":
    try:
        # 设置标准输出为UTF-8编码
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        # 如果设置失败，继续使用默认编码
        pass

def main():
    """系统主入口"""
    print("="*75)
    print("🎓 Scholar - 6-Agent 混合路由学术工作流引擎")
    print("="*75)
    print("\n📖 系统建制说明：")
    print("   1. 🧠 主控 (Lead Author)   - 深度破题统稿 (DeepSeek-R1 官方)")
    print("   2. 🔍 检索员 (Searcher)    - 外部 API 寻源 (Semantic Scholar + 秘塔)")
    print("   3. 📦 提取员 (Extractor)   - 权威性加权 (Citation Velocity 算法)")
    print("   4. 📖 审查员 (Reviewer)    - RAG超长上下文找 Gap (SiliconFlow Kimi)")
    print("   5. 🕷️ 采集员 (Crawler)     - 动态爬虫编写与清洗 (SiliconFlow V3.2)")
    print("   6. 📈 分析员 (Analyst)     - CSV统计检验与绘图 (SiliconFlow V3.2)")
    print()
    
    # --- 优雅的环境连通性检测  ---
    if config.use_llm():
        print("✅ 检测到环境变量中配置了有效的 API Key，系统准备点火...")
        # 注意：因为这里采用了双平台，且底层 Agent 做了 lazy load，
        # 所以我们把深度测试留给各 Agent 初始化时自动进行。
    else:
        print("⚠️ 未检测到任何 API Key，将强制使用 Mock 兜底模式运行！")
    
    # 实例化工作流
    workflow = SixAgentWorkflow()
    
    # 🌟 默认测试课题
    default_idea = """
    基于大语言模型（LLM）情感分析与另类数据的金融市场量化交易策略实证研究。
    具体要求：
    1. 梳理近三年关于"非结构化另类数据（Alternative Data，如社交媒体、新闻情绪）在量化预测中应用"的顶级金融或计算机文献。
    2. 审查员深入探讨现有的开源语言模型在金融垂直领域的局限性（Research Gaps）。
    3. 数据分析硬性需求：请数据分析员编写 Python 脚本，生成过去180天某虚拟科技资产的"每日新闻情感得分（-1到1）"与"次日资产收益率"的模拟数据集（样本量180）。对两者进行皮尔逊相关性分析（Pearson Correlation）和 OLS 线性回归检验，并绘制包含拟合线与置信区间的回归散点图（请使用 seaborn）。
    4. 字数与排版：最终的 Markdown 论文不少于 3000 字，必须将实证数据结果与第二章的理论完美融合，并在文末列出真实的参考文献。
    """
    
    # --- 交互式输入逻辑 ---
    print("\n" + "="*75)
    print("💡 请输入您的研究课题 (直接回车将使用默认课题)")
    print("="*75)

    if len(sys.argv) > 1:
        # 优先使用命令行参数
        idea = sys.argv[1]
        print(f"检测到命令行参数，使用课题: {idea}")
    else:
        # 否则尝试交互式输入
        try:
            user_input = input("请输入课题 > ").strip()
            if user_input:
                idea = user_input
            else:
                idea = default_idea
                print("使用默认课题...")
        except KeyboardInterrupt:
            print("\n用户取消操作。")
            return

    print(f"\n🚀 启动研究课题: {idea.strip()}")
    project = workflow.run(idea)
    
    # --- 恢复你的精美执行报表 ---
    print("\n" + "="*75)
    print("📋 项目执行摘要报告")
    print("="*75)
    
    print(f"\n📂 项目 ID: {project.id}")
    print(f"🚦 最终状态: {project.status}")
    print(f"📝 系统运行日志: 共 {len(project.logs)} 条节点记录")
    
    print("\n📊 产出统计：")
    print(f"   • 大纲章节: {len(project.plan.get('outline', []))} 章")
    print(f"   • 入库文献: {project.stored_papers.get('chroma_count', 0)} 篇 (按权威度重排)")
    print(f"   • 发现硬核 Gap: {len(project.review.get('research_gaps', []))} 个")
    print(f"   • 生成数据图表: {len(project.data_results.get('charts', []))} 张")
    print(f"   • 最终论文长度: {len(project.final_paper)} 字符")
    
    print("\n" + "="*75)
    print("📄 论文引言预览 (前 800 字符)")
    print("="*75)
    print(project.final_paper[:800] + "...\n")

if __name__ == "__main__":
    main()