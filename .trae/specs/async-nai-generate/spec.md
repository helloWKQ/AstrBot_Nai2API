# 异步生图功能 Spec

## Why

当前 LLM 调用生图时需要等待图片生成完成（30-60秒）才能回复，这导致：
- 机器人在这段时间无法响应群里的其他消息
- 随着生图次数增加，机器人回复延迟越来越高
- 用户体验差，不知道机器人是否在工作中

## What Changes

- 新增**异步生图模式**：LLM 调用生图后立即返回，后台异步生成图片
- 新增 3 个可选消息参数：前置消息、成功消息、失败消息
- 新增**插件配置项**：是否开启异步模式、最大并发数
- 生图成功时：图片在上、消息在下，消息引用用户消息（不@）
- 生图失败时：发送失败消息

## Impact

- Affected specs: nai_generate 工具
- Affected code: `main.py`、插件配置 `__init__.py`、README.md

## ADDED Requirements

### Requirement: 异步生图模式

当开启异步模式时，LLM 调用 `nai_generate` 工具的行为变更如下：

#### Scenario: 正常生图流程
- **WHEN** LLM 调用 `nai_generate` 并提供 `pre_message`、`success_message`、`failure_message`
- **THEN** 立即发送 `pre_message`（如果不为空）
- **THEN** 后台异步执行生图任务
- **THEN** 生图成功后，发送图片 + `success_message`（图片在上，消息在下）
- **THEN** 消息引用用户原始消息（不@）

#### Scenario: 生图失败流程
- **WHEN** 后台生图任务失败
- **THEN** 发送 `failure_message`
- **THEN** 消息引用用户原始消息（不@）

#### Scenario: 生图成功（pre_message 为空）
- **WHEN** `pre_message` 为空字符串
- **THEN** 不发送前置消息，直接后台生图
- **THEN** 生图成功后直接发送图片 + `success_message`

### Requirement: 并发控制

- 系统最多同时执行 **N** 个生图任务（N 可配置，默认 3）
- 当并发数已满时，新任务进入**排队队列**
- 队列中的任务按顺序执行（FIFO）

### Requirement: 插件配置项

插件配置面板新增以下选项：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `async_generate` | 开关 | `false` | 是否开启异步生图模式 |
| `max_concurrent` | 数字 | `3` | 最大并发生图数 |

- 当 `async_generate=false` 时，行为与之前一致（同步生图）
- `max_concurrent` 仅在 `async_generate=true` 时生效

### Requirement: 图片 + 消息发送格式

生图成功时的消息格式：
```
[图片]
引用用户消息
success_message
```

## MODIFIED Requirements

### Requirement: nai_generate 工具参数变更

新增 3 个可选参数：

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `pre_message` | string | `""` | 生图前发送的消息（异步模式下使用） |
| `success_message` | string | `""` | 生图成功后发送的消息（异步模式下使用） |
| `failure_message` | string | `""` | 生图失败后发送的消息（异步模式下使用） |

- 这些参数仅在 `async_generate=true` 时生效
- 当 `async_generate=false` 时，这些参数被忽略

## REMOVED Requirements

无

## 技术实现要点

1. 使用 `asyncio.create_task()` 创建后台任务
2. 使用 `asyncio.Semaphore` 控制并发数
3. 使用 `queue.Queue` 实现任务排队
4. 引用消息使用 `MessageSegment.reply()` 不带 `@`
