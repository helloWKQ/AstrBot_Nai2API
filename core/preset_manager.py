"""
质量前缀预设管理

内置常用预设，支持用户自定义保存/删除。
"""

import json
from pathlib import Path

from astrbot.api import logger


# 内置预设（来自 Nai2API 官方前端 app.js 中的 artistPresets）
BUILTIN_PRESETS: dict[str, dict[str, str]] = {
    "2.5D唯美风": {
        "artist": "0.9::misaka_12003-gou ::, dino_(dinoartforame), wanke, liduke, year 2025, realistic, 4k, -2::green ::, textless version, The image is highly intricate finished drawn. Only the character's face is in anime style, but their body is in realistic style. 1.35::A highly finished photo-style artwork that has lively color, graphic texture, realistic skin surface, and lifelike flesh with little obliques::. 1.63::photorealistic::, 1.63::photo(medium)::, \\n20::best quality, absurdres, very aesthetic, detailed, masterpiece::,, very aesthetic, masterpiece, no text,",
        "desc": "2.5D唯美风（Nai2API 默认）",
    },
    "韩漫小清新风": {
        "artist": "[[[artist:dishwasher1910]]], {{yd_(orange_maru)}}, [artist:ciloranko], [artist:sho_(sho_lwlw)], [ningen mame], year 2024,",
        "desc": "韩漫小清新风格",
    },
    "本子动漫风": {
        "artist": "1.4::asanagi::,{{{{{artist:asanagi}}}}},1.2::xiaoluo_xl::,1.3::Artist: misaka_12003-gou::,1.2::Artist:shexyo::,0.7::Artist:b.sa_(bbbs)::,1::Artist:qiandaiyiyu::,1.05::artist:natedecock::,1.05::artist:kunaboto::,0.75::artist:kandata_nijou::,1.05::artist:zer0.zer0 ::,1.05::artist:jasony::,0.75::misaka_12003-gou ::, dino_(dinoartforame), wanke, liduke, year 2025, realistic, 4k, -2::green ::, {textless version, The image is highly intricate finished drawn,write realistically,true to life}, 1.35::A highly finished photo-style artwork that has lively color, graphic texture, realistic skin surface, and lifelike flesh with little obliques::, 1.63::photorealistic::,3::age slider::,1.63::photo(medium)::, 2::best quality, absurdres, very aesthetic, detailed, masterpiece::,-4::Muscle definition, abs::",
        "desc": "本子动漫风格",
    },
    "GalGame风": {
        "artist": "artist:ningen_mame,, noyu_(noyu23386566),, toosaka asagi,, location,\\n20::best quality, absurdres, very aesthetic, detailed, masterpiece::,:,, very aesthetic, masterpiece, no text,",
        "desc": "GalGame 风格",
    },
    "动漫风": {
        "artist": "artist collaboration, 0.70::artist:necomi ::, 0.80::artist:tan (tangent) ::, 1.38::artist:kanda done ::, 1.22::artist:quasarcake ::, 1.22::artist:atdan ::, 0.94::artist:fuumi (radial engine) ::, 1.70::artist:john kafka ::, 0.60::artist:meisansan ::, 0.98::artist:ogipote ::, 0.44::artist:nixeu ::, 0.74::artist:mignon ::, 0.94::artist:rangu ::, 1.18::artist:hiten (hitenkei) ::, 1.24::artist:freng ::, 0.56::artist:miwabe sakura ::, year 2024, perspective",
        "desc": "动漫风（旧版画师混合）",
    },
}


class PresetManager:
    """预设管理器"""

    def __init__(self, data_dir: Path):
        self._preset_file = data_dir / "presets.json"
        self._custom_presets: dict[str, dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        if self._preset_file.exists():
            try:
                with open(self._preset_file, "r", encoding="utf-8") as f:
                    self._custom_presets = json.load(f)
                logger.info("[PresetManager] 已加载 %d 个自定义预设", len(self._custom_presets))
            except Exception as e:
                logger.warning("[PresetManager] 加载预设文件失败: %s", e)
                self._custom_presets = {}

    def _save(self) -> None:
        self._preset_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._preset_file, "w", encoding="utf-8") as f:
            json.dump(self._custom_presets, f, ensure_ascii=False, indent=2)

    def get(self, name: str) -> str | None:
        """获取预设的 artist 值，返回 None 表示预设不存在"""
        # 优先查自定义预设
        if name in self._custom_presets:
            return self._custom_presets[name]["artist"]
        # 再查内置预设
        if name in BUILTIN_PRESETS:
            return BUILTIN_PRESETS[name]["artist"]
        return None

    def list_all(self) -> dict[str, dict[str, str]]:
        """列出所有预设（内置 + 自定义），自定义覆盖同名内置"""
        result = dict(BUILTIN_PRESETS)
        result.update(self._custom_presets)
        return result

    def save(self, name: str, artist: str, desc: str = "") -> None:
        """保存自定义预设"""
        self._custom_presets[name] = {
            "artist": artist.strip(),
            "desc": desc.strip() or f"自定义预设",
        }
        self._save()
        logger.info("[PresetManager] 已保存预设 '%s'", name)

    def delete(self, name: str) -> bool:
        """删除自定义预设，返回是否成功"""
        if name not in self._custom_presets:
            return False
        del self._custom_presets[name]
        self._save()
        logger.info("[PresetManager] 已删除预设 '%s'", name)
        return True

    def update(self, name: str, artist: str | None = None, desc: str | None = None) -> bool:
        """修改自定义预设，返回是否成功。只传 artist 就只改 artist，只传 desc 就只改 desc。"""
        if name not in self._custom_presets:
            return False
        if artist is not None:
            self._custom_presets[name]["artist"] = artist.strip()
        if desc is not None:
            self._custom_presets[name]["desc"] = desc.strip()
        self._save()
        logger.info("[PresetManager] 已修改预设 '%s'", name)
        return True

    def is_builtin(self, name: str) -> bool:
        return name in BUILTIN_PRESETS
