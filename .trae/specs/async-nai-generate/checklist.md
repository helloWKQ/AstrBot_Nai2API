# Checklist

## 配置项
- [ ] `async_generate` 配置项存在且默认为 false
- [ ] `max_concurrent` 配置项存在且默认为 3
- [ ] README.md 中有配置说明

## 工具参数
- [ ] `nai_generate_tool` 包含 `pre_message` 参数
- [ ] `nai_generate_tool` 包含 `success_message` 参数
- [ ] `nai_generate_tool` 包含 `failure_message` 参数

## 异步逻辑
- [ ] 使用 `asyncio.Semaphore` 控制并发
- [ ] 使用 `asyncio.create_task()` 启动后台任务
- [ ] 当 `async_generate=false` 时，行为与之前一致（同步）
- [ ] 当 `async_generate=true` 时，立即发送 pre_message（如果不为空）

## 消息发送格式
- [ ] 生图成功后图片在上、消息在下
- [ ] 图片下方显示"预设名 | 耗时X秒"
- [ ] 预设名正确显示（使用预设时显示预设名，否则显示"无预设"）
- [ ] 耗时显示正确（秒）
- [ ] 消息引用用户原始消息（不带 @）
- [ ] 生图失败时发送 failure_message

## 并发控制
- [ ] 同时最多执行 `max_concurrent` 个生图任务
- [ ] 超出限制的任务排队等待

## 文档
- [ ] CHANGELOG.md 更新
- [ ] README.md LLM 工具文档更新
