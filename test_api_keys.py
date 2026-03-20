#!/usr/bin/env python3
"""
API密钥状态检查脚本
用于验证.env文件中的API密钥配置状态
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 定义要检查的API密钥
KEYS_TO_CHECK = [
    ('DEEPSEEK_KEY', 'DeepSeek (主控Agent)'),
    ('SILICONFLOW_KEY', 'SiliconFlow (审查员Agent)'),
    ('METASO_API_KEY', 'Metaso秘塔 (检索员Agent)'),
    ('IEEE_API_KEY', 'IEEE Xplore (学术数据库)'),
    ('CORE_API_KEY', 'CORE API (备用数据源)'),
    ('OPENAI_API_KEY', 'OpenAI (备用)'),
    ('SEMANTIC_SCHOLAR_API_KEY', 'Semantic Scholar (英文检索)'),
]

# 占位符模式（安全配置）
PLACEHOLDER_PATTERNS = [
    'sk-your-',
    'your-',
    'mk-your-',
    'example-',
    'placeholder',
    'test-',
    'demo-',
]

def is_placeholder(value):
    """检查是否为占位符值"""
    if not value:
        return False
    value_lower = value.lower()
    for pattern in PLACEHOLDER_PATTERNS:
        if value_lower.startswith(pattern):
            return True
    return False

def check_api_keys():
    """检查所有API密钥状态"""
    # Windows兼容的打印
    try:
        print("=" * 60)
        print("API密钥安全状态检查")
        print("=" * 60)
    except UnicodeEncodeError:
        # 使用ASCII字符
        print("=" * 60)
        print("API Key Security Check")
        print("=" * 60)

    results = []
    all_secure = True

    for env_var, service in KEYS_TO_CHECK:
        value = os.getenv(env_var, '')

        if not value:
            status = "[X] Not set"
            security = "Safe (empty)"
            all_secure = all_secure and True
        elif is_placeholder(value):
            status = "[!] Placeholder"
            security = "Safe (template)"
            all_secure = all_secure and True
        elif len(value) < 10:
            status = "[!] Too short"
            security = "[!] Possibly invalid"
            all_secure = False
        else:
            # 检查是否为泄露的密钥
            if env_var == 'DEEPSEEK_KEY' and value == 'REDACTED-DEEPSEEK-KEY':
                status = "[CRITICAL] LEAKED KEY"
                security = "EMERGENCY RISK"
                all_secure = False
            elif env_var == 'SILICONFLOW_KEY' and value == 'REDACTED-SILICONFLOW-KEY':
                status = "[CRITICAL] LEAKED KEY"
                security = "EMERGENCY RISK"
                all_secure = False
            elif env_var == 'METASO_API_KEY' and value == 'REDACTED-METASO-KEY':
                status = "[CRITICAL] LEAKED KEY"
                security = "EMERGENCY RISK"
                all_secure = False
            elif env_var == 'IEEE_API_KEY' and value == 'REDACTED-IEEE-KEY':
                status = "[CRITICAL] LEAKED KEY"
                security = "EMERGENCY RISK"
                all_secure = False
            elif env_var == 'CORE_API_KEY' and value == 'REDACTED-CORE-KEY':
                status = "[CRITICAL] LEAKED KEY"
                security = "EMERGENCY RISK"
                all_secure = False
            else:
                status = "[OK] Set"
                security = "[SAFE] Real key"
                all_secure = all_secure and True

        results.append((service, env_var, value[:10] + '...' if len(value) > 13 else value, status, security))

    # 打印结果
    print(f"{'Service':<25} {'Env Var':<20} {'Value':<15} {'Status':<15} {'Security':<15}")
    print("-" * 90)

    for service, env_var, value, status, security in results:
        print(f"{service:<25} {env_var:<20} {value:<15} {status:<15} {security:<15}")

    print("\n" + "=" * 60)
    print("Security Assessment:")

    if all_secure:
        print("[OK] All API keys are safe")
        print("   - No leaked keys detected")
        print("   - All keys are empty, placeholders, or new secure keys")
    else:
        print("[CRITICAL] Security risks detected!")
        print("   Please follow steps in API_KEY_EMERGENCY_RESPONSE.md")
        print("   Revoke leaked keys and generate new ones immediately")

    # 检查系统功能
    print("\n" + "=" * 60)
    print("System Function Check:")

    try:
        from config import config
        can_use_llm = config.use_llm()
        print(f"LLM service available: {'[OK] Yes' if can_use_llm else '[ERROR] No'}")

        # 检查各Agent配置
        print("\nAgent configuration status:")
        for agent_name, agent_config in config.agents.items():
            provider = agent_config.get('provider', 'Not set')
            model = agent_config.get('model', 'Not set')
            print(f"  {agent_name}: {provider}/{model}")

    except ImportError as e:
        print(f"[ERROR] Cannot import config module: {e}")
    except Exception as e:
        print(f"[ERROR] Configuration check error: {e}")

    print("=" * 60)

if __name__ == "__main__":
    try:
        check_api_keys()
    except UnicodeEncodeError:
        # 如果还有编码问题，使用更简单的输出
        import os
        from dotenv import load_dotenv
        load_dotenv()

        print("API Key Status (ASCII only):")
        print("-" * 50)
        for env_var, service in KEYS_TO_CHECK:
            value = os.getenv(env_var, '')
            if value:
                print(f"{service}: {'[SET]' if value else '[EMPTY]'}")
            else:
                print(f"{service}: [EMPTY]")