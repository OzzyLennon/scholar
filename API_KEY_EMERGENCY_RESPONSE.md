# API密钥紧急响应指南
**生成时间**: 2026-03-20
**紧急程度**: 🔴 CRITICAL - 立即行动

## 🔴 泄露的API密钥 (已确认)
以下5个API密钥已确认在`.env`文件中泄露，必须立即撤销：

### 1. DeepSeek (最高风险)
- **密钥**: `REDACTED-DEEPSEEK-KEY`
- **用途**: 主控Agent (Lead Author) - 规划+决策+统稿
- **撤销地址**: https://platform.deepseek.com/api_keys
- **优先级**: 🟥 最高 - 主模型，成本风险最高

### 2. SiliconFlow (高风险)
- **密钥**: `REDACTED-SILICONFLOW-KEY`
- **用途**: 审查员Agent (Reviewer) - 文献综述+寻找研究空白
- **撤销地址**: https://siliconflow.cn/console/api-key
- **优先级**: 🟥 高 - 使用昂贵的长文本模型

### 3. Metaso秘塔 (中风险)
- **密钥**: `REDACTED-METASO-KEY`
- **用途**: 采集员Agent (Searcher) - 中文文献深度检索
- **撤销地址**: https://metaso.cn/user/api-keys
- **优先级**: 🟧 中 - 中文检索服务

### 4. IEEE Xplore (中风险)
- **密钥**: `REDACTED-IEEE-KEY`
- **用途**: IEEE学术文献检索
- **撤销地址**: https://developer.ieee.org/myapps
- **优先级**: 🟧 中 - 学术数据库访问

### 5. CORE API (低风险)
- **密钥**: `REDACTED-CORE-KEY`
- **用途**: 备用数据源
- **撤销地址**: https://core.ac.uk/services/api
- **优先级**: 🟨 低 - 备用服务

## 🚨 立即行动步骤

### 第一阶段：密钥撤销（1小时内完成）
按以下顺序访问各平台撤销密钥：

1. **DeepSeek** (立即行动)
   - 登录 https://platform.deepseek.com/api_keys
   - 找到密钥 `REDACTED-DEEPSEEK-KEY`
   - 点击"撤销"或"删除"
   - ✅ 记录撤销时间: _____

2. **SiliconFlow** (30分钟内)
   - 登录 https://siliconflow.cn/console/api-key
   - 删除泄露密钥
   - ✅ 记录操作时间: _____

3. **Metaso秘塔** (1小时内)
   - 登录 https://metaso.cn/user/api-keys
   - 重置泄露密钥
   - ✅ 记录操作时间: _____

4. **IEEE Xplore** (2小时内)
   - 登录 https://developer.ieee.org/myapps
   - 找到对应应用重置API密钥
   - ✅ 记录操作时间: _____

5. **CORE API** (4小时内)
   - 登录 https://core.ac.uk/services/api
   - 账户设置中重置API密钥
   - ✅ 记录操作时间: _____

### 第二阶段：新密钥生成
撤销后立即在各平台生成新密钥：

1. **DeepSeek新密钥**: `________________________`
2. **SiliconFlow新密钥**: `________________________`
3. **Metaso新密钥**: `________________________`
4. **IEEE Xplore新密钥**: `________________________`
5. **CORE API新密钥**: `________________________`

**存储位置建议**: 使用密码管理器（如Bitwarden、1Password）或加密笔记保存。

## 🛡️ 当前安全状态

### ✅ 已完成的保护措施
1. **泄露源隔离**: `.env.leaked.backup` 已创建，原`.env`文件被移除
2. **安全配置**: 使用`.env.example`创建了空白的`.env`文件
3. **Git防护**: `.gitignore`已配置忽略`.env`文件
4. **历史干净**: git历史中没有`.env`文件提交记录

### ⚠️ 需要人工操作
所有API密钥必须**手动访问对应平台**进行撤销和重新生成。

## 📋 验证检查清单

完成每个步骤后请勾选：

### 密钥撤销
- [ ] DeepSeek密钥已撤销
- [ ] SiliconFlow密钥已撤销
- [ ] Metaso密钥已撤销
- [ ] IEEE Xplore密钥已撤销
- [ ] CORE API密钥已撤销

### 新密钥生成
- [ ] DeepSeek新密钥已生成并记录
- [ ] SiliconFlow新密钥已生成并记录
- [ ] Metaso新密钥已生成并记录
- [ ] IEEE Xplore新密钥已生成并记录
- [ ] CORE API新密钥已生成并记录

### 配置更新
- [ ] 新密钥已填入`.env`文件
- [ ] 系统功能测试通过
- [ ] 使用监控已启用（各平台）

## 🔧 配置更新脚本

更新`.env`文件后，运行验证：

```bash
# 验证所有API密钥已设置
python test_api_keys.py

# 测试配置加载
python -c "from config import config; print('Config loaded:', config.use_llm())"
```

## 📞 紧急联系人

**平台客服** (如密钥被滥用导致费用异常):
- DeepSeek客服: support@deepseek.com
- SiliconFlow客服: support@siliconflow.cn
- IEEE技术支持: contactcenter@ieee.org

## 🕒 时间记录

| 操作 | 计划时间 | 实际完成时间 | 备注 |
|------|----------|--------------|------|
| DeepSeek撤销 | 立即 | _____ |  |
| SiliconFlow撤销 | 30分钟内 | _____ |  |
| Metaso撤销 | 1小时内 | _____ |  |
| IEEE撤销 | 2小时内 | _____ |  |
| CORE撤销 | 4小时内 | _____ |  |
| 所有新密钥生成 | 今日内 | _____ |  |
| 配置更新完成 | 今日内 | _____ |  |
| 功能验证完成 | 今日内 | _____ |  |

---

**重要提醒**: 泄露的API密钥可能已被用于未经授权的API调用，请立即检查各平台的用量监控，如有异常费用请立即联系平台客服。