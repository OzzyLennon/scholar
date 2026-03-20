# Scholar项目安全策略

## 概述
Scholar是一个6-Agent学术工作流引擎，涉及多个第三方API服务。本文档定义了项目的安全策略、最佳实践和应急响应流程。

## 安全原则

### 1. 最小权限原则
- API密钥应仅授予项目所需的最小权限
- 定期审查和撤销不再需要的密钥

### 2. 密钥不落地原则
- 绝对不在代码中硬编码API密钥
- 绝对不提交`.env`文件到版本控制系统
- 使用环境变量或安全的密钥管理系统

### 3. 轮换原则
- API密钥应定期轮换（建议90天）
- 出现安全事件时立即轮换所有受影响密钥

## 密钥管理

### 密钥类型
| 服务商 | 用途 | 风险等级 | 轮换周期 |
|--------|------|----------|----------|
| DeepSeek | 主控Agent | 🔴 高风险 | 90天 |
| SiliconFlow | 审查员Agent | 🔴 高风险 | 90天 |
| Metaso秘塔 | 中文检索 | 🟡 中风险 | 180天 |
| IEEE Xplore | 学术数据库 | 🟡 中风险 | 180天 |
| CORE API | 备用数据源 | 🟢 低风险 | 180天 |

### 密钥存储
1. **本地开发**:
   - 使用`.env`文件（在`.gitignore`中）
   - 复制`.env.example`为`.env`
   - 填入真实密钥

2. **生产环境**:
   - 使用环境变量
   - 或使用密钥管理服务（如AWS Secrets Manager, HashiCorp Vault）

3. **备份**:
   - 在密码管理器中备份所有API密钥
   - 记录密钥生成日期和过期日期

## 泄露应急响应流程

### 步骤1：立即隔离
```bash
# 如果发现.env文件被意外提交
git rm --cached .env
echo ".env" >> .gitignore
git commit -m "Remove .env from tracking"
```

### 步骤2：撤销泄露密钥
按优先级顺序：
1. DeepSeek (最高风险)
2. SiliconFlow (高风险)
3. Metaso秘塔 (中风险)
4. IEEE Xplore (中风险)
5. CORE API (低风险)

### 步骤3：生成新密钥
1. 在各自平台生成新密钥
2. 记录到密码管理器
3. 更新所有环境的配置

### 步骤4：监控使用
1. 检查各平台的用量监控
2. 设置用量告警阈值
3. 如有异常费用立即联系客服

## 开发安全规范

### 代码审查检查项
- [ ] 没有硬编码的API密钥
- [ ] `.env`文件在`.gitignore`中
- [ ] 使用`.env.example`作为模板
- [ ] 没有提交敏感数据文件

### 提交前检查
```bash
# 检查是否有敏感文件被意外添加
git status

# 检查.gitignore是否有效
git check-ignore .env

# 如果有敏感文件被跟踪，立即移除
git rm --cached path/to/sensitive/file
```

## 安全工具配置

### .gitignore配置
确保以下内容在`.gitignore`中：
```
# API密钥
.env
.env.local
*.env

# 密钥文件
*_key.txt
*_secret.txt
*_token.txt

# 数据文件
*.csv
local_store.json
*.db

# 日志文件
*.log
logs/
```

### pre-commit检查（可选）
创建`.pre-commit-config.yaml`防止提交敏感信息。

## 审计与监控

### 定期审计
| 审计项目 | 频率 | 负责人 |
|----------|------|--------|
| 密钥轮换状态 | 每月 | 项目管理员 |
| 用量监控 | 每周 | 技术负责人 |
| 安全配置审查 | 每季度 | 安全负责人 |

### 监控指标
1. **API调用频率** - 异常增加可能表示滥用
2. **费用趋势** - 突然增加可能表示泄露
3. **错误率** - 高错误率可能表示密钥失效或被撤销

## 事件报告

### 内部报告流程
1. 发现泄露 → 立即通知技术负责人
2. 技术负责人启动应急响应
3. 完成响应后编写事件报告

### 外部报告
如涉及第三方服务：
- 立即联系平台客服
- 提供事件时间线和影响范围
- 跟进处理进展

## 附录

### 平台联系方式
- **DeepSeek**: support@deepseek.com
- **SiliconFlow**: support@siliconflow.cn
- **IEEE**: contactcenter@ieee.org
- **CORE**: support@core.ac.uk

### 密钥生成地址
1. DeepSeek: https://platform.deepseek.com/api_keys
2. SiliconFlow: https://siliconflow.cn/console/api-key
3. Metaso秘塔: https://metaso.cn/user/api-keys
4. IEEE Xplore: https://developer.ieee.org/myapps
5. CORE API: https://core.ac.uk/services/api

### 历史安全事件
- **2026-03-20**: API密钥泄露事件
  - 原因: `.env`文件包含真实密钥（本地文件安全风险）
  - 响应: 立即撤销所有5个泄露密钥，生成新密钥
  - 改进: 完善安全文档和.gitignore配置

---

**最后更新**: 2026-03-20
**版本**: 1.0
**负责人**: 项目安全委员会