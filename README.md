# astrbot_plugin_nai2api

通过 [Nai2API](https://github.com/STA1N156/Nai2API) 网关调用 NovelAI 生成图片的 AstrBot 插件。

## 功能

- `/nai` 指令文生图，支持尺寸、预设、质量前缀、负面提示词、随机种子
- LLM Tool 调用生图（AI 助手可直接调用）
- 5 个内置预设（来自 Nai2API 官方前端）+ 自定义预设保存/删除
- 支持普通/2K/4K 分辨率
- 图片本地缓存，自动清理
- 配套人格提示词（生图助手），无需手动写英文标签

## 前置要求

- 运行中的 [Nai2API](https://github.com/STA1N156/Nai2API) 服务
- Nai2API 用户密钥（`STA1N-xxx` 格式，在 Nai2API 后台生成）

## 安装

将 `astrbot_plugin_nai2api` 目录放入 AstrBot 的 `data/plugins/` 下，重启 AstrBot。

## 配置

在 AstrBot 管理面板 → 插件配置中填写：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `api_url` | Nai2API 服务地址 | `https://nai.sta1n.cn` |
| `token` | 用户密钥（必填） | 空 |
| `default_model` | 默认模型 | `nai-diffusion-4-5-full` |
| `default_size` | 默认尺寸 | `竖图` |
| `default_steps` | 默认步数 | `28` |
| `default_scale` | 默认提示词引导值 | `6` |
| `default_cfg` | 默认 CFG rescale（0-1） | `0` |
| `default_sampler` | 默认采样器 | `k_dpmpp_2m_sde` |
| `default_negative` | 默认负面提示词 | Nai2API 官方默认 |
| `default_artist` | 默认画师串/质量前缀 | 2.5D唯美风（Nai2API 官方默认） |
| `default_noise_schedule` | 默认噪声调度 | `karras` |
| `timeout` | 请求超时(秒) | `120` |
| `llm_tool_enabled` | 允许 LLM 调用生图（AI 助手需要） | `true` |
| `allow_2k` | 允许生成 2K 图片（关闭后自动降级为普通尺寸，防误扣 15 点） | `true` |
| `allow_4k` | 允许生成 4K 图片（关闭后自动降级为普通尺寸，防误扣 25 点） | `true` |
| `max_cached_images` | 图片最大缓存数 | `50` |

> **重要**：如果要让 AI 助手自动调用生图，请确保 `llm_tool_enabled` 为 `true`，
> 并启用 AstrBot 人格中引用的生图助手人格提示词。

---

## 使用方式

本插件提供**两种使用方式**，根据你的习惯选择：

### 方式一：AI 助手自动画图（推荐新手）

配置好人格提示词后，直接用中文跟 AI 说你想要什么，
AI 会自动把你的描述翻译成英文标签并调用生图。

```
用户：帮我画一个银发蓝眼的女孩，站在雨夜霓虹街头
AI → 自动调用 nai_generate 生成图片

用户：来一张 2K 高清壁纸，二次元风景，日落
AI → 自动调用 nai_generate 生成图片

用户：帮我画个 GalGame 风格的女生，穿校服
AI → 自动调用 nai_generate 生成图片
```

> 使用方式一需要配置"生图助手"人格提示词，详见下方【人格提示词】章节。

### 方式二：手动写 `/nai` 指令

直接在 `/nai` 后面写英文关键词（NovelAI 风格）：

```
/nai 1girl, silver hair, blue eyes
```

**指定图片尺寸** — 在提示词前面加尺寸关键词：

```
/nai 竖图 1girl, silver hair          → 832×1216（默认）
/nai 横图 1girl, silver hair          → 1216×832
/nai 方图 1girl, silver hair          → 1024×1024
/nai 2K竖图 1girl, silver hair        → 1088×1600（扣15点）
/nai 4K横图 1girl, silver hair        → 1984×1344（扣25点）
```

> 不写尺寸就是竖图。

**使用预设** — 预设就是一组提前配好的"质量前缀"：

```
/nai -p GalGame风 1girl, silver hair  → 自动加 ningen_mame 等画师前缀
/nai -p 动漫风 1girl, silver hair      → 自动加多画师混合前缀
/nai 2K竖图 -p 韩漫小清新风 1girl      → 尺寸和预设可以组合
```

> 不写 `-p` 就用默认的 2.5D唯美风质量前缀。

**自定义质量前缀** — 用 `--artist` 临时指定，不用保存预设：

```
/nai 1girl --artist best quality, absurdres
/nai 1girl --artist artist:ningen_mame,, very aesthetic
```

**指定负面提示词** — 用 `--negative` 添加不想要的内容：

```
/nai 1girl --negative bad anatomy, bad hands, text
```

> 不写 `--negative` 就用配置里的默认负面提示词。

**指定随机种子** — 用 `--seed` 固定随机种子，相同种子+相同参数可复现图片：

```
/nai 1girl --seed 12345
```

> 不写 `--seed` 则每次随机。

**组合使用** — 尺寸、预设、负面提示词、种子可以随意组合：

```
/nai 2K竖图 -p GalGame风 1girl --negative low quality --seed 42
```

**预设管理**

```
/nai presets                              查看所有预设（也可用 /nai 预设）
/nai presets <预设名>                      查看单个预设详情（也可用 /nai 预设 <预设名>）
/nai save 我的预设 best quality, detailed  保存自定义预设（也可用 /nai 保存）
/nai del 我的预设                          删除自定义预设（也可用 /nai 删除）
```

> **小提示**：`save` 命令以「第一个空格」分割名称和质量前缀，所以预设名称不能含空格。
> 例如 `/nai save 我的预设 best quality, absurdres` → 名称=`我的预设`，质量前缀=`best quality, absurdres`。
> 如果想修改已保存的预设，用同样的名称重新保存即可覆盖。

**查询余额** — 查看你的 Nai2API 剩余点数：

```
/nai balance    或  /nai 余额  /nai 点数  /nai 次数
```

返回示例：
```
Nai2API 余额查询
  剩余点数: 86 点
  账号状态: 正常
  ---
  预计可生成:
    普通尺寸(竖图/横图/方图): ~86 张
    2K尺寸: ~5 张
    4K尺寸: ~3 张
```

**内置预设** — 来自 Nai2API 官方前端，和网页版完全一致：

| 预设名 | 说明 |
|--------|------|
| 2.5D唯美风 | Nai2API 默认，半写实半动漫风格 |
| 韩漫小清新风 | 韩式漫画清新风格 |
| 本子动漫风 | 日系本子风格，多画师混合 |
| GalGame风 | 游戏CG风格（ningen_mame 等画师） |
| 动漫风 | 旧版多画师混合动漫风格 |

**尺寸与费用**

| 尺寸 | 分辨率 | Nai2API 扣点 |
|------|--------|-------------|
| 竖图 | 832×1216 | 1 |
| 横图 | 1216×832 | 1 |
| 方图 | 1024×1024 | 1 |
| 2K竖图 | 1088×1600 | 15 |
| 2K横图 | 1600×1088 | 15 |
| 2K方图 | 1344×1344 | 15 |
| 4K竖图 | 1344×1984 | 25 |
| 4K横图 | 1984×1344 | 25 |
| 4K方图 | 1728×1728 | 25 |

---

## 人格提示词（生图助手）

本插件配套一个 AstrBot 人格提示词，让 AI 助手自动帮你画图。
文件位置：`persona/nai_artist_persona.md`

人格提示词包含：
- 角色设定（活泼有耐心的 AI 生图助手）
- 中文描述 → NovelAI 英文标签的翻译规则
- 提示词结构和质量词排序技巧
- nai_generate 工具调用规范（何时调用、参数如何填）
- 回复格式（调用前/成功/失败如何回应用户）
- 多轮对话迭代技巧（改姿势/换场景/调风格/保持 seed 微调）
- 常用提示词模板（二次元/写实/风景/GalGame CG）
- 常见元素中英文对照表（发色/发型/瞳色/服装/表情/动作/场景/光影/质量词）

### 配置步骤

**步骤 1**：确保插件配置中 `llm_tool_enabled = true`（默认已开启）

**步骤 2**：打开 AstrBot 管理后台 → 找到「人格与情景」或「Persona」面板

**步骤 3**：新建一个人格，起个名字（如「生图助手」或「AI 画师」）

**步骤 4**：将 `persona/nai_artist_persona.md` 的内容复制粘贴到人格的 System Prompt 中

**步骤 5**：将这个人格设为默认人格，或在对话中切换到该人格

**步骤 6**：直接用中文跟 AI 说你想要什么，它会自动生成图片

### 对话示例

```
用户：帮我画一个银发蓝眼的女孩，站在雨夜霓虹街头
AI：好的，正在为你生成... ✨
    [自动调用 nai_generate 工具]
    [图片发送给用户]
    这是根据你的描述生成的图片，喜欢吗？😊

用户：换个横图风景的，日落海边
AI：收到，马上画一张日落海景 🎨
    [自动调用 nai_generate 工具，size="横图"]
    [图片发送给用户]
    画面中你最满意的部分是哪里？如果想调整可以告诉我～

用户：再画一张 GalGame 风格的校服女生
AI：来啦，正在用 AI 画笔创作... 🖌️
    [自动调用 nai_generate 工具，preset="GalGame风"]
    [图片发送给用户]
    这是第 1 张，想要不同风格/姿势/服装可以继续说！
```

### 小技巧

- 想改图？可以对 AI 说"换个姿势"、"换个场景"、"更写实一点"等
- 想提高清晰度？说"来一张 2K 高清版"或"4K 超清版"
- 想微调但保持画面风格？让 AI 记录同一个 seed 再调整
- 想探索不同风格？问 AI"这个预设里有什么风格？"

---

## LLM 工具调用（开发者参考）

当 `llm_tool_enabled` 开启时，AI 助手可通过以下工具调用：

### nai_generate - 生成图片

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `prompt` | string | 是 | 英文关键词提示词，逗号分隔 |
| `size` | string | 否 | 尺寸，如"竖图"、"横图"、"2K竖图"等 |
| `artist` | string | 否 | 质量前缀/画师串，如"best quality, absurdres" |
| `negative` | string | 否 | 负面提示词，留空用默认 |
| `preset` | string | 否 | 预设名称，如"高质量"、"动漫风"、"GalGame风" |
| `seed` | int | 否 | 随机种子，0 表示自动随机 |

**参数优先级**：`artist` > `preset` > 默认（2.5D唯美风）

### nai_get_balance - 查询余额

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| 无 | - | - | 直接调用，返回账户余额和可生成图片数量 |

### nai_list_presets - 预设管理

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `preset_name` | string | 否 | 指定预设名称查看详情，留空列出所有预设 |

### nai_save_preset - 保存预设

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 预设名称（不能含空格） |
| `artist` | string | 是 | 质量前缀/画师串 |

### nai_delete_preset - 删除预设

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | 要删除的预设名称（内置预设无法删除） |

---

## 参数优先级（指令方式）

`--artist` > `-p 预设` > 配置中的 `default_artist`

即手动指定的 `--artist` 会覆盖预设，预设会覆盖默认配置。

---

## 目录结构

```
astrbot_plugin_nai2api/
├── main.py                 # 插件入口，/nai 指令和 LLM Tool 注册
├── metadata.yaml           # 插件元数据
├── _conf_schema.json       # 配置 Schema
├── requirements.txt        # 依赖声明
├── README.md               # 本文件
├── core/
│   ├── nai2api_client.py   # Nai2API 客户端（/generate 请求）
│   ├── image_manager.py    # 图片保存和缓存管理
│   └── preset_manager.py   # 预设加载和保存
└── persona/
    └── nai_artist_persona.md  # 生图助手人格提示词（System Prompt）
```
