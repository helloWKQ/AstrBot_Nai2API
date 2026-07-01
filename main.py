"""
Nai2API AstrBot 生图插件

通过 Nai2API 网关调用 NovelAI 生成图片。
支持 /nai 指令和 LLM 工具调用。
"""

import re
import time
from pathlib import Path

import mcp

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Node, Plain
from astrbot.api.star import Context, Star, StarTools
from astrbot.core.star.filter.command import GreedyStr

from .core.image_manager import ImageManager
from .core.nai2api_client import Nai2ApiClient, DEFAULT_ARTIST, DEFAULT_NEGATIVE
from .core.preset_manager import PresetManager

# 解析用户输入中的尺寸前缀、-p/--preset、--artist 和 --negative 参数
_SIZE_PATTERN = re.compile(
    r'^(2K竖图|2K横图|2K方图|4K竖图|4K横图|4K方图|竖图|横图|方图)\s+',
    re.IGNORECASE,
)
_PRESET_PATTERN = re.compile(r'(?:-p|--preset)\s+(\S+)', re.IGNORECASE)
_SEED_PATTERN = re.compile(r'--seed\s+(\d+)', re.IGNORECASE)
_ARTIST_PATTERN = re.compile(r'--artist\s+(.+?)(?=\s+(?:--negative|-p|--preset|--seed)\s+|$)', re.DOTALL)
_NEGATIVE_PATTERN = re.compile(r'--negative\s+(.+?)(?=\s+(?:--artist|-p|--preset|--seed)\s+|$)', re.DOTALL)


def _parse_nai_command(text: str) -> tuple[str | None, str, str | None, str | None, str | None, int | None]:
    """
    解析 /nai 指令的参数。

    格式: /nai [尺寸] <提示词> [-p <预设>] [--artist <质量前缀>] [--negative <负面提示词>] [--seed <种子>]

    Returns:
        (size, prompt, preset_name, artist, negative, seed)
    """
    text = text.strip()
    size = None

    # 提取尺寸前缀
    m = _SIZE_PATTERN.match(text)
    if m:
        size = m.group(1)
        text = text[m.end():]

    # 提取预设名
    preset_name = None
    m = _PRESET_PATTERN.search(text)
    if m:
        preset_name = m.group(1)
        text = text[:m.start()] + text[m.end():]

    # 提取种子
    seed = None
    m = _SEED_PATTERN.search(text)
    if m:
        seed = int(m.group(1))
        text = text[:m.start()] + text[m.end():]

    # 提取负面提示词
    negative = None
    m = _NEGATIVE_PATTERN.search(text)
    if m:
        negative = m.group(1).strip()
        text = text[:m.start()] + text[m.end():]

    # 提取质量前缀/画师串
    artist = None
    m = _ARTIST_PATTERN.search(text)
    if m:
        artist = m.group(1).strip()
        text = text[:m.start()] + text[m.end():]

    prompt = text.strip()
    return size, prompt, preset_name, artist, negative, seed


class Nai2ApiPlugin(Star):
    """Nai2API 生图插件"""

    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.data_dir = StarTools.get_data_dir("astrbot_plugin_nai2api")

        api_url = str(config.get("api_url", "https://nai.sta1n.cn")).strip()
        token = str(config.get("token", "")).strip()
        timeout = int(config.get("timeout", 120))
        max_cached = int(config.get("max_cached_images", 50))

        self.client = Nai2ApiClient(
            api_url=api_url,
            token=token,
            default_size=str(config.get("default_size", "竖图")),
            default_model=str(config.get("default_model", "nai-diffusion-4-5-full")),
            default_steps=int(config.get("default_steps", 28)),
            default_scale=int(config.get("default_scale", 6)),
            default_cfg=float(config.get("default_cfg", 0)),
            default_sampler=str(config.get("default_sampler", "k_dpmpp_2m_sde")),
            default_negative=str(config.get("default_negative", DEFAULT_NEGATIVE)),
            default_artist=str(config.get("default_artist", DEFAULT_ARTIST)),
            default_noise_schedule=str(config.get("default_noise_schedule", "karras")),
            allow_2k=bool(config.get("allow_2k", True)),
            allow_4k=bool(config.get("allow_4k", True)),
            timeout=timeout,
        )

        self.imgr = ImageManager(
            data_dir=self.data_dir,
            max_cached=max_cached,
            timeout=timeout,
        )

        self.presets = PresetManager(self.data_dir)

        self._llm_tool_enabled = bool(config.get("llm_tool_enabled", True))
        self._show_image_info = bool(config.get("show_image_info", True))

    async def terminate(self):
        """插件卸载时清理资源"""
        await self.client.close()
        await self.imgr.close()

    def _resolve_artist(self, preset_name: str | None, artist: str | None) -> str | None:
        """解析 artist：预设优先，--artist 覆盖预设"""
        if artist is not None:
            return artist
        if preset_name is not None:
            resolved = self.presets.get(preset_name)
            if resolved is not None:
                return resolved
        return None

    def _forward_result(self, event: AstrMessageEvent, title: str, content: str):
        """将查询结果以合并转发消息形式发送，不占用聊天空间"""
        node = Node(
            uin=int(event.get_sender_id()) if event.get_sender_id().isdigit() else 0,
            name=event.message_obj.sender.nickname if hasattr(event.message_obj.sender, 'nickname') else "查询结果",
            content=[Plain(f"{title}\n\n{content}")]
        )
        return event.chain_result([node])

    async def _send_image_with_info(self, event: AstrMessageEvent, image_path: Path, preset_name: str | None, elapsed: float):
        """发送图片+信息标签"""
        # 先发图片
        await event.send(event.image_result(str(image_path)))

        # 如果开启了信息标签，则发送标签
        if self._show_image_info:
            info_text = f"{preset_name or '默认'} | 耗时{int(elapsed)}秒"
            await event.send(event.plain_result(info_text))

    async def _do_generate(
        self,
        prompt: str,
        size: str | None = None,
        artist: str | None = None,
        negative: str | None = None,
        seed: int | None = None,
    ) -> Path:
        """执行生图并返回本地图片路径"""
        image_bytes = await self.client.generate(
            prompt, size=size, artist=artist, negative=negative, seed=seed
        )
        return await self.imgr.save_image(image_bytes)

    @filter.command("nai")
    async def nai_generate(self, event: AstrMessageEvent, args: GreedyStr):
        """NovelAI 生图

        用法: /nai [尺寸] <提示词> [-p <预设>] [--artist <质量前缀>] [--negative <负面提示词>] [--seed <种子>]
              /nai presets | /nai 预设  →  查看所有预设
              /nai save <名称> <质量前缀>  →  保存自定义预设
              /nai del <名称>  →  删除自定义预设
        """
        # 注意：AstrBot 的 filter.command 已经把 wake_prefix（如 "/"）和 "nai" 前缀去除
        # 因此 args 就是命令后的完整原始文本，不需要再去除前缀
        args = args.strip() if args else ""

        # 子命令：预设列表 / 查看单个预设
        if args == "presets" or args == "预设" or args.startswith("presets ") or args.startswith("预设 "):
            preset_name = args[8:].strip() if args.startswith("presets ") else args[3:].strip() if args.startswith("预设 ") else ""
            return self._handle_presets(event, preset_name)

        # 子命令：查询余额
        if args in ("balance", "余额", "点数", "次数"):
            return await self._handle_balance(event)

        # 子命令：save <名称> <质量前缀>（中英文别名）
        if args.startswith("save ") or args.startswith("保存 "):
            rest = args[5:].strip() if args.startswith("save ") else args[3:].strip()
            return self._handle_save_preset(event, rest)

        # 子命令：del <名称>（中英文别名）
        if args.startswith("del ") or args.startswith("删除 "):
            rest = args[4:].strip() if args.startswith("del ") else args[3:].strip()
            return self._handle_del_preset(event, rest)

        # 无参数时显示帮助
        if not args:
            return event.plain_result(
                "用法: /nai [尺寸] <提示词> [-p <预设>] [--artist <质量前缀>] [--negative <负面提示词>]\n"
                "预设: /nai presets(预设) | /nai save(保存) <名称> <质量前缀> | /nai del(删除) <名称>\n"
                "余额: /nai balance(余额/点数/次数)\n"
                "尺寸: 竖图|横图|方图|2K竖图|2K横图|2K方图|4K竖图|4K横图|4K方图\n\n"
                "示例:\n"
                "  /nai 1girl, silver hair\n"
                "  /nai -p 高质量 1girl, silver hair\n"
                "  /nai 2K竖图 -p 动漫风 1girl, silver hair\n"
                "  /nai 1girl --artist best quality, absurdres\n"
                "  /nai 1girl --negative bad anatomy, bad hands\n"
                "  /nai 1girl --seed 12345\n"
                "  /nai save 我的预设 best quality, absurdres, detailed\n"
                "  /nai 保存 我的预设 best quality, absurdres, detailed\n"
                "  /nai del 我的预设\n"
                "  /nai 删除 我的预设\n"
                "  /nai balance"
            )

        size, prompt, preset_name, artist, negative, seed = _parse_nai_command(args)

        if not prompt:
            return event.plain_result("提示词不能为空")

        # 解析 artist（预设 + --artist 优先级）
        final_artist = self._resolve_artist(preset_name, artist)

        # 预设不存在时提示
        if preset_name and self.presets.get(preset_name) is None and artist is None:
            return event.plain_result(f"预设 '{preset_name}' 不存在，使用 /nai presets 查看可用预设")

        try:
            start = time.time()
            image_path = await self._do_generate(
                prompt, size=size, artist=final_artist, negative=negative, seed=seed
            )
            elapsed = time.time() - start
            await self._send_image_with_info(event, image_path, preset_name, elapsed)
            return None
        except Exception as e:
            logger.error("[Nai2API] 生图失败: %s", e)
            # 失败时也显示信息标签
            if self._show_image_info:
                elapsed = time.time() - start
                reason = str(e)[:20] if str(e) else "未知错误"
                info_text = f"{preset_name or '默认'} | 耗时{int(elapsed)}秒\n失败原因：{reason}"
                return event.plain_result(info_text)
            return event.plain_result(f"生图失败: {e}")

    async def _handle_balance(self, event: AstrMessageEvent):
        """查询 Nai2API 余额"""
        try:
            data = await self.client.get_balance()
            balance = data.get("balance", 0)
            enabled = data.get("enabled", True)
            note = data.get("note", "")

            balance_int = int(balance)
            normal_count = balance_int
            count_2k = balance_int // 15
            count_4k = balance_int // 25

            status = "正常" if enabled else "已禁用"
            lines = [
                f"剩余点数: {balance_int} 点",
                f"账号状态: {status}",
            ]
            if note:
                lines.append(f"备注: {note}")
            lines.append(f"---")
            lines.append(f"预计可生成:")
            lines.append(f"  普通尺寸(竖图/横图/方图): ~{normal_count} 张")
            lines.append(f"  2K尺寸: ~{count_2k} 张")
            lines.append(f"  4K尺寸: ~{count_4k} 张")

            return self._forward_result(event, "Nai2API 余额查询", "\n".join(lines))
        except Exception as e:
            logger.error("[Nai2API] 查询余额失败: %s", e)
            return event.plain_result(f"查询余额失败: {e}")

    def _handle_presets(self, event: AstrMessageEvent, preset_name: str = ""):
        """处理预设列表 / 查看单个预设"""
        all_presets = self.presets.list_all()
        
        if preset_name:
            if preset_name in all_presets:
                info = all_presets[preset_name]
                builtin_tag = " [内置]" if self.presets.is_builtin(preset_name) else ""
                desc = info.get("desc", "")
                artist_val = info.get("artist", "")
                return self._forward_result(
                    event,
                    f"预设 '{preset_name}'{builtin_tag}",
                    f"描述: {desc}\n质量前缀:\n{artist_val}"
                )
            else:
                return event.plain_result(f"预设 '{preset_name}' 不存在，使用 /nai presets 查看可用预设")
        
        if not all_presets:
            return event.plain_result("暂无预设")

        lines = []
        for name, info in all_presets.items():
            builtin_tag = " [内置]" if self.presets.is_builtin(name) else ""
            desc = info.get("desc", "")
            artist_val = info.get("artist", "")
            lines.append(f"{name}{builtin_tag} - {desc}")
            lines.append(f"  {artist_val[:80]}{'...' if len(artist_val) > 80 else ''}")
            lines.append("")

        lines.append("使用: /nai -p <预设名> <提示词>")
        lines.append("查看单个预设详情: /nai presets <预设名>")
        return self._forward_result(event, "可用预设列表", "\n".join(lines))

    def _handle_save_preset(self, event: AstrMessageEvent, args: str):
        """保存自定义预设"""
        args = args.strip()
        if not args:
            return event.plain_result("用法: /nai save <名称> <质量前缀>\n示例: /nai save 我的预设 best quality, absurdres, detailed")

        parts = args.split(None, 1)
        if len(parts) < 2:
            return event.plain_result("用法: /nai save <名称> <质量前缀>\n示例: /nai save 我的预设 best quality, absurdres, detailed")

        name, artist = parts[0].strip(), parts[1].strip()
        if not name or not artist:
            return event.plain_result("名称和质量前缀不能为空")

        is_overwrite = self.presets.get(name) is not None
        self.presets.save(name, artist)
        action = "已更新" if is_overwrite else "已保存"
        return event.plain_result(f"{action}预设 '{name}': {artist}")

    def _handle_del_preset(self, event: AstrMessageEvent, args: str):
        """删除自定义预设"""
        name = args.strip()
        if not name:
            return event.plain_result("用法: /nai del <名称>")

        if self.presets.is_builtin(name):
            return event.plain_result(f"'{name}' 是内置预设，无法删除")

        if self.presets.delete(name):
            return event.plain_result(f"已删除预设 '{name}'")
        else:
            return event.plain_result(f"预设 '{name}' 不存在")

    @filter.llm_tool(name="nai_generate")
    async def nai_generate_tool(
        self,
        event: AstrMessageEvent,
        prompt: str,
        size: str = "",
        artist: str = "",
        negative: str = "",
        preset: str = "",
        seed: str = "0",
    ):
        """使用 NovelAI 生成图片。

        Args:
            prompt(string): 图片提示词，例如 "1girl, silver hair, blue eyes"
            size(string): 图片尺寸，可选 "竖图"、"横图"、"方图"、"2K竖图" 等，留空使用默认
            artist(string): 质量前缀或画师串，例如 "best quality, absurdres"，留空使用默认或预设
            negative(string): 负面提示词，留空使用默认
            preset(string): 预设名称，例如 "高质量"、"动漫风"，留空使用默认
            seed(string): 随机种子，数字字符串，"0" 表示自动随机，相同种子可复现图片
        """
        if not self._llm_tool_enabled:
            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(type="text", text="生图功能已被管理员禁用")]
            )

        if not prompt.strip():
            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(type="text", text="提示词不能为空")]
            )

        final_artist = self._resolve_artist(
            preset.strip() or None,
            artist.strip() or None,
        )

        try:
            seed_int = 0
            if seed and seed.strip():
                try:
                    seed_int = int(seed)
                except ValueError:
                    seed_int = 0
            final_seed = seed_int if seed_int else None

            start = time.time()
            image_path = await self._do_generate(
                prompt.strip(),
                size=size.strip() or None,
                artist=final_artist,
                negative=negative.strip() or None,
                seed=final_seed,
            )
            elapsed = time.time() - start

            await self._send_image_with_info(event, image_path, preset.strip() or None, elapsed)

            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(
                    type="text",
                    text=f"图片已生成并发送给用户。提示词: {prompt.strip()[:100]}"
                )]
            )
        except Exception as e:
            logger.error("[Nai2API] LLM 工具生图失败: %s", e)
            # 失败时也显示信息标签
            if self._show_image_info:
                elapsed = time.time() - start
                reason = str(e)[:20] if str(e) else "未知错误"
                info_text = f"{preset.strip() or '默认'} | 耗时{int(elapsed)}秒\n失败原因：{reason}"
                await event.send(event.plain_result(info_text))
            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(type="text", text=f"生图失败: {e}")]
            )

    @filter.llm_tool(name="nai_get_balance")
    async def nai_get_balance_tool(self, event: AstrMessageEvent, detail: str = "simple"):
        """查询 Nai2API 账户余额和剩余点数。

        Args:
            detail(string): 可选，返回详细程度，"simple" 精简版，"full" 完整版，留空默认 simple
        """
        try:
            data = await self.client.get_balance()
            balance = data.get("balance", 0)
            enabled = data.get("enabled", True)
            note = data.get("note", "")

            balance_int = int(balance)
            normal_count = balance_int
            count_2k = balance_int // 15
            count_4k = balance_int // 25

            status = "正常" if enabled else "已禁用"
            lines = [
                f"剩余点数: {balance_int} 点",
                f"账号状态: {status}",
            ]
            if note:
                lines.append(f"备注: {note}")
            lines.append(f"---")
            lines.append(f"预计可生成:")
            lines.append(f"  普通尺寸(竖图/横图/方图): ~{normal_count} 张")
            lines.append(f"  2K尺寸: ~{count_2k} 张")
            lines.append(f"  4K尺寸: ~{count_4k} 张")

            result_text = "\n".join(lines)
            await event.send(self._forward_result(event, "Nai2API 余额查询", result_text))
            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(type="text", text=result_text)]
            )
        except Exception as e:
            logger.error("[Nai2API] LLM 查询余额失败: %s", e)
            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(type="text", text=f"查询余额失败: {e}")]
            )

    @filter.llm_tool(name="nai_list_presets")
    async def nai_list_presets_tool(self, event: AstrMessageEvent, preset_name: str = ""):
        """列出所有可用预设，或查看单个预设详情。

        Args:
            preset_name(string): 可选，指定要查看的预设名称，留空则列出所有预设
        """
        all_presets = self.presets.list_all()
        
        if preset_name:
            if preset_name in all_presets:
                info = all_presets[preset_name]
                builtin_tag = " [内置]" if self.presets.is_builtin(preset_name) else ""
                desc = info.get("desc", "")
                artist_val = info.get("artist", "")
                result_text = f"描述: {desc}\n质量前缀:\n{artist_val}"
                await event.send(self._forward_result(event, f"预设 '{preset_name}'{builtin_tag}", result_text))
                return mcp.types.CallToolResult(
                    content=[mcp.types.TextContent(type="text", text=result_text)]
                )
            else:
                result_text = f"预设 '{preset_name}' 不存在，可用预设: {', '.join(all_presets.keys())}"
                await event.send(event.plain_result(result_text))
                return mcp.types.CallToolResult(
                    content=[mcp.types.TextContent(type="text", text=result_text)]
                )
        
        if not all_presets:
            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(type="text", text="暂无预设")]
            )

        lines = []
        for name, info in all_presets.items():
            builtin_tag = " [内置]" if self.presets.is_builtin(name) else ""
            desc = info.get("desc", "")
            lines.append(f"{name}{builtin_tag} - {desc}")

        result_text = "\n".join(lines)
        await event.send(self._forward_result(event, "可用预设列表", result_text))
        return mcp.types.CallToolResult(
            content=[mcp.types.TextContent(type="text", text=result_text)]
        )

    @filter.llm_tool(name="nai_save_preset")
    async def nai_save_preset_tool(
        self,
        event: AstrMessageEvent,
        name: str,
        artist: str,
    ):
        """保存自定义预设。

        Args:
            name(string): 预设名称（不能含空格）
            artist(string): 质量前缀/画师串
        """
        name = name.strip()
        artist = artist.strip()
        
        if not name or not artist:
            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(type="text", text="预设名称和质量前缀都不能为空")]
            )

        if " " in name:
            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(type="text", text="预设名称不能包含空格，请使用下划线或其他字符")]
            )

        is_overwrite = self.presets.get(name) is not None
        self.presets.save(name, artist)
        action = "已更新" if is_overwrite else "已保存"
        result_text = f"{action}预设 '{name}' 成功"
        await event.send(event.plain_result(result_text))
        return mcp.types.CallToolResult(
            content=[mcp.types.TextContent(type="text", text=result_text)]
        )

    @filter.llm_tool(name="nai_delete_preset")
    async def nai_delete_preset_tool(self, event: AstrMessageEvent, name: str):
        """删除自定义预设。

        Args:
            name(string): 要删除的预设名称
        """
        name = name.strip()
        
        if not name:
            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(type="text", text="预设名称不能为空")]
            )

        if self.presets.is_builtin(name):
            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(type="text", text=f"'{name}' 是内置预设，无法删除")]
            )

        if self.presets.delete(name):
            result_text = f"已删除预设 '{name}'"
            await event.send(event.plain_result(result_text))
            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(type="text", text=result_text)]
            )
        else:
            result_text = f"预设 '{name}' 不存在"
            await event.send(event.plain_result(result_text))
            return mcp.types.CallToolResult(
                content=[mcp.types.TextContent(type="text", text=result_text)]
            )
