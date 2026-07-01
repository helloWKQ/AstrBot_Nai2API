# 更新日志

## v1.0.11

- 真正修复 Gemini 等模型通过 OpenAI 兼容层调用 LLM 工具时报 `value at top-level must be a list` 错误的问题
- 根本原因：AstrBot 框架 `register_llm_tool` / `spec_to_func` 生成的 JSON Schema 不包含 `required` 字段，Gemini API 对工具 Schema 校验严格，缺少 `required` 字段时返回 400 错误
- 修复方案：在插件初始化后，手动给 5 个 LLM 工具的 `parameters` 添加 `required` 字段，绕过框架限制
- 涉及工具：`nai_generate`(prompt)、`nai_get_balance`(detail)、`nai_list_presets`(preset_name)、`nai_save_preset`(name, artist)、`nai_delete_preset`(name)
- v1.0.10 的"必填参数"方案无效，因为框架根本不根据参数默认值生成 `required` 字段

## v1.0.10

- 彻底修复 Gemini 等模型通过 OpenAI 兼容层调用 LLM 工具时报 `value at top-level must be a list` 错误的问题
- 根本原因：AstrBot 框架 `spec_to_func` 生成 JSON Schema 时不设置 `required` 字段，当工具所有参数都有默认值（零必填）时，Gemini 校验失败
- 将 `nai_get_balance` 的 `detail` 参数改为必填（去掉默认值 `"simple"`）
- 将 `nai_list_presets` 的 `preset_name` 参数改为必填（去掉默认值 `""`），内部逻辑重写：填 "all"/"全部" 列出所有预设，填具体名称查看单个预设
- 至此所有 5 个 LLM 工具均至少有一个必填参数，Schema 生成正常

## v1.0.9

- 修复 LLM 工具调用与部分 AI 模型（如 Gemini）的兼容性问题
- 将 `nai_generate` 工具的 `seed` 参数从 int 类型改为 string 类型，避免 Schema 验证错误
- 为 `nai_get_balance` 工具添加 `detail` 参数，解决零参数导致的 Schema 生成问题
- 函数内部自动处理类型转换，不影响正常使用

## v1.0.8

- 新增 `AI_MODIFY_RULES.md` AI 修改要点文档（记录修改规范、退回方法、沟通注意事项）
- 补更新 CHANGELOG.md 和 README.md（之前漏掉了）
- 开发者说明：零基础新手

## v1.0.7

- 生图成功后显示信息标签：`预设名 | 耗时X秒`
- 生图失败时也显示信息标签，包含简要失败原因
- 插件配置新增 `show_image_info` 开关（默认开启）
- 指令生图和 LLM 工具生图都支持

## v1.0.6

- 修复合并转发消息功能丢失的问题（合并分支时被覆盖）
- 恢复查询类结果使用合并转发消息发送（余额查询、预设列表）
- 图片文件名包含提示词，方便服务器上查找管理

## v1.0.5

- 生成的图片文件名包含提示词（清洗后），方便在服务器上查找和管理

## v1.0.4

- 新增 CHANGELOG.md 更新日志文件

## v1.0.3

- 查询类结果（余额查询、预设列表）改用合并转发消息发送，不再刷屏

## v1.0.2

- 添加 LLM 工具调用：查询余额（nai_get_balance）
- 添加 LLM 工具调用：预设管理（nai_list_presets、nai_save_preset、nai_delete_preset）
- 修复 LLM 工具调用结果不发送给用户的问题

## v1.0.1

- 修复 `/nai save` 指令参数丢失的问题
- 添加查看单个预设详情功能（`/nai presets <预设名>`）

## v1.0.0

- 初始版本
- `/nai` 指令文生图，支持尺寸、预设、质量前缀、负面提示词、随机种子
- LLM Tool 调用生图（nai_generate）
- 5 个内置预设 + 自定义预设保存/删除
- 支持普通/2K/4K 分辨率
- 图片本地缓存，自动清理
- 配套人格提示词（生图助手）
