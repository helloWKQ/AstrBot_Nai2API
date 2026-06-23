# 图片信息标签功能 规格说明

## Why
用户希望在每次生成图片发送时，能显示"预设名"+"耗时"+"秒"，方便知道用了什么预设、生成了多久。

## What Changes
- 生成图片后，在图片下方添加一行文字：`预设名 | 耗时X秒`
- 插件配置增加开关 `show_image_info`（默认开启）
- 不影响现有任何功能

## Impact
- 受影响的功能：指令生图、LLM 工具生图（所有生图流程）
- 受影响的文件：main.py、_conf_schema.json

## ADDED Requirements

### Requirement: 图片信息标签
系统 SHALL 在每次生成图片发送时，在图片下方附带一行信息标签

#### Scenario: 生图成功时
- **WHEN** 用户触发生图（指令或 LLM）
- **THEN** 发送图片后，在图片下方跟一行文字，格式为：`预设名 | 耗时X秒`
- **AND** 如果没有预设，显示：`默认 | 耗时X秒`

#### Scenario: 生图失败时
- **WHEN** 生图过程中发生错误
- **THEN** 发送一行文字，格式为：`预设名 | 耗时X秒\n失败原因：XXX`
- **AND** 失败原因简洁明了，不超过 20 个字符
- **AND** 如果没有预设，显示：`默认 | 耗时X秒`

#### Scenario: 插件配置控制
- **WHEN** 用户在插件设置中关闭 `show_image_info`
- **THEN** 生图时不再发送信息标签，只发图片

## MODIFIED Requirements

### Requirement: 插件配置项
**MODIFIED**: 增加 `show_image_info` 配置项
- 类型：布尔值
- 默认值：`true`（开启）
- 说明：开启后在图片下方显示预设名和耗时
