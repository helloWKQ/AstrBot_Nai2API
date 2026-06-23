# Tasks

## Task 1: 添加插件配置项

在插件配置中添加异步模式开关和最大并发数配置。

- [ ] Task 1.1: 在 `__init__.py` 中添加配置项 `async_generate`（布尔值，默认 false）和 `max_concurrent`（整数，默认 3）
- [ ] Task 1.2: 在 README.md 中添加配置说明

## Task 2: 修改 nai_generate 工具参数

扩展 LLM 工具 `nai_generate` 的参数列表。

- [ ] Task 2.1: 在 `nai_generate_tool` 方法中添加 `pre_message`、`success_message`、`failure_message` 三个参数

## Task 3: 实现异步生图核心逻辑

创建后台任务调度器和并发控制机制。

- [ ] Task 3.1: 在 `NaiImagePlugin` 类中添加 `asyncio.Semaphore` 用于并发控制
- [ ] Task 3.2: 创建 `_async_generate` 私有方法，处理异步生图和消息发送
- [ ] Task 3.3: 修改 `nai_generate_tool`，当开启异步模式时：
  - 发送 `pre_message`（如果不为空）
  - 用 `asyncio.create_task()` 启动后台任务
  - 立即返回结果给 LLM

## Task 4: 实现图片 + 消息发送格式

确保生图成功的消息格式正确。

- [ ] Task 4.1: 实现图片在上、消息在下的发送格式
- [ ] Task 4.2: 实现引用用户消息（不带 @）

## Task 5: 测试和文档

- [ ] Task 5.1: 更新 CHANGELOG.md
- [ ] Task 5.2: 更新 README.md 中 LLM 工具调用文档

## Task Dependencies

- Task 2 依赖 Task 1（需要先有配置项）
- Task 3 依赖 Task 1 和 Task 2
- Task 4 依赖 Task 3
- Task 5 依赖 Task 1-4
