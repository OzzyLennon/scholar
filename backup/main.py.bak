# ==========================================
# Scholar - 5-Agent 学术工作流引擎
# ==========================================
from openai import OpenAI
from workflow import FiveAgentWorkflow
from config import config

def main():
    """主入口"""
    print("="*70)
    print("🎓 Scholar - 5-Agent 学术工作流引擎")
    print("="*70)
    print("\n📖 架构说明：")
    print("   1. 🧠 主控 (Lead Author)   - 破题规划 + 路径决策 + 最终统稿")
    print("   2. 🔍 检索员 (Searcher)    - 按主控指令搜索文献")
    print("   3. 📦 提取员 (Extractor)   - 清洗数据 → 存入 Zotero/ChromaDB")
    print("   4. 📖 审查员 (Reviewer)    - RAG检索 → 提炼Research Gap")
    print("   5. 📊 数据研究员 (Data)    - 动态唤醒 → Python沙箱 → 生成图表")
    print()
    
    # 初始化 LLM 客户端
    client = None
    llm_available = False
    
    if config.use_llm():
        try:
            test_client = OpenAI(
                api_key=config.OPENAI_API_KEY or config.DEEPSEEK_API_KEY,
                base_url=config.OPENAI_BASE_URL if config.OPENAI_API_KEY else config.DEEPSEEK_BASE_URL
            )
            # 简单测试连接
            test_client.models.list()
            client = test_client
            llm_available = True
            print("✅ 检测到 API Key 且网络畅通，启用真实 LLM")
        except Exception as e:
            print(f"⚠️ API Key 已配置但连接失败: {str(e)[:50]}...")
            print("⚠️ 自动回退到 Mock 模式")
    else:
        print("⚠️ 未配置 API Key，使用 Mock 模式")
    
    # 创建工作流引擎（不传入 client，让 Agent 自动初始化各自的 LLM）
    workflow = FiveAgentWorkflow()
    
    # 示例课题
    test_idea = """
    我想研究一下如何利用 Python 自动化脚本提高传统文献收集的效率。
    需要对比传统方法和自动化方法的差异，分析效率提升的数据。
    """
    
    # 运行工作流
    project = workflow.run(test_idea)
    
    # 输出摘要
    print("\n" + "="*70)
    print("📋 项目执行摘要")
    print("="*70)
    
    print(f"\n项目ID: {project.id}")
    print(f"状态: {project.status}")
    print(f"执行日志: {len(project.logs)} 条")
    
    print("\n📊 工作流统计：")
    print(f"   • 大纲章节: {len(project.plan.get('outline', []))}")
    print(f"   • 检索文献: {len(project.papers)} 篇")
    print(f"   • 向量存储: {project.stored_papers.get('chroma_count', 0)} 条")
    print(f"   • 研究空白: {len(project.review.get('research_gaps', []))} 个")
    print(f"   • 数据分析: {'是' if project.data_results else '否'}")
    print(f"   • 论文长度: {len(project.final_paper)} 字符")
    
    # 显示论文预览
    print("\n" + "="*70)
    print("📄 论文预览 (前 800 字符)")
    print("="*70)
    print(project.final_paper[:800] + "...\n")

if __name__ == "__main__":
    main()
