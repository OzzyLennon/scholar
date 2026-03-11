# ==========================================
# Scholar - 6-Agent 学术工作流引擎 (究极完全体)
# ==========================================
from workflow import SixAgentWorkflow
from config import config

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
    
    # 🌟 测试你的爬虫+分析双链能力
    test_idea = """
    我想研究目前 Github 上人工智能 Agent 框架的发展热度。
    请帮我爬取 Github Trending 页面 (https://github.com/trending/python?since=monthly) 。
    提取出排名前列的项目名称，并对星标情况做简单趋势分析，生成柱状图直观展示。
    """
    
    print(f"\n🚀 启动研究课题: {test_idea.strip()}")
    project = workflow.run(test_idea)
    
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