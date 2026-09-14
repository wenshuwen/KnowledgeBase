#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""归档数据层的回归测试。

覆盖四类容易在后期静默坏掉的地方：
  1. 索引 ↔ 文件双向一致（跨月合并改了文件位置，索引不跟着改就是全线 404）；
  2. 日包结构契约（组数、每组条数下限、GitHub 四板块与链接白名单）；
  3. 按月合并的幂等与索引指向改写；
  4. 分组分布（同类内容不能全被摊进同一组）。

以及一条针对真实仓库的断言：**线上看到的归档结构必须通过整套契约校验**。

运行：
    /Users/tigerwen/.workbuddy/binaries/python/envs/default/bin/python -m pytest site/tests -q
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Iterator

import pytest

SITE_DIR = Path(__file__).resolve().parent.parent
for extra in (str(SITE_DIR), str(SITE_DIR / "tools")):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import archive as arc  # noqa: E402

TMP_ROOT = Path(__file__).resolve().parent / ".tmp_archive"


# --------------------------------------------------------------------------- #
# 夹具与构造器
# --------------------------------------------------------------------------- #


def _gh_item(i: int, section: str = "skills") -> dict[str, Any]:
    return {
        "name": f"owner-{section}-{i}/repo-{i}",
        "url": f"https://github.com/owner-{section}-{i}/repo-{i}",
        "stars": 1000 + i,
        "desc": "示例项目",
        "descEn": "Sample project",
        "scene": "适合用于测试工程。",
        "lang": "Python",
        "topics": ["testing"],
    }


def _group(i: int, pad: int = 0) -> dict[str, Any]:
    """造一组刚好满足下限的内容。pad 用于造出「多于下限」的场景。"""
    return {
        "questions": [
            {"cat": "theory" if i % 2 == 0 else "perf", "q": f"问题{i}-{j}", "a": "答案"}
            for j in range(arc.GROUP_MIN["questions"] + pad)
        ],
        "knowledge": [
            {"cat": "theory", "t": f"知识点{i}-{j}", "body": "正文"}
            for j in range(arc.GROUP_MIN["knowledge"] + pad)
        ],
        "skills": [
            {"cat": "auto", "e": "🛠", "t": f"技能{i}-{j}", "d": "描述", "tools": ["pytest"]}
            for j in range(arc.GROUP_MIN["skills"] + pad)
        ],
        "pitfalls": [
            {"t": f"坑{i}-{j}", "d": "描述", "tip": "破解"}
            for j in range(arc.GROUP_MIN["pitfalls"] + pad)
        ],
        "exam": [
            {"cat": "theory", "q": f"选择题{i}-{j}", "o": ["A", "B", "C", "D"], "a": 0, "x": "解析"}
            for j in range(arc.GROUP_MIN["exam"] + pad)
        ],
    }


def _pack(date_str: str, pad: int = 0) -> dict[str, Any]:
    return {
        "date": date_str,
        "generatedAt": f"{date_str}T20:00:00",
        "groupCount": arc.GROUP_COUNT,
        "groups": [_group(i, pad) for i in range(arc.GROUP_COUNT)],
        "github": {sec: [_gh_item(i, sec) for i in range(arc.GITHUB_MIN)]
                   for sec in arc.GITHUB_SECTIONS},
    }


@pytest.fixture()
def tmp_arch(monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """把 ARCHIVE_DIR 指向仓库内的临时目录（系统临时目录在受限环境下建不了）。"""
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT, ignore_errors=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(arc, "ARCHIVE_DIR", TMP_ROOT)
    try:
        yield TMP_ROOT
    finally:
        shutil.rmtree(TMP_ROOT, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 1. 日包结构契约
# --------------------------------------------------------------------------- #


def test_valid_pack_passes() -> None:
    assert arc.validate_pack(_pack("2026-09-12")) == []


def test_pack_missing_groups_is_rejected() -> None:
    pack = _pack("2026-09-12")
    pack["groups"] = []
    assert any("groups" in p for p in arc.validate_pack(pack))


def test_pack_with_too_few_groups_is_rejected() -> None:
    pack = _pack("2026-09-12")
    pack["groups"] = pack["groups"][: arc.GROUP_COUNT - 1]
    assert any("组数不足" in p for p in arc.validate_pack(pack))


@pytest.mark.parametrize("key", sorted(arc.GROUP_MIN))
def test_pack_with_short_module_is_rejected(key: str) -> None:
    """任一模块条数低于下限都要报出来 —— 下限是自动化的生成目标。"""
    pack = _pack("2026-09-12")
    pack["groups"][1][key] = pack["groups"][1][key][: arc.GROUP_MIN[key] - 1]
    problems = arc.validate_pack(pack)
    assert any(key in p and "不足" in p for p in problems), problems


@pytest.mark.parametrize("section", arc.GITHUB_SECTIONS)
def test_github_section_must_reach_min(section: str) -> None:
    pack = _pack("2026-09-12")
    pack["github"][section] = pack["github"][section][: arc.GITHUB_MIN - 1]
    assert any(section in p for p in arc.validate_pack(pack))


def test_pack_with_bad_date_is_rejected() -> None:
    pack = _pack("2026-09-12")
    pack["date"] = "2026/09/12"
    assert any("date" in p for p in arc.validate_pack(pack))


# --------------------------------------------------------------------------- #
# 2b. cat 词表（归档短键 vs wiki 长键，混用会让前端标签变成英文原键）
# --------------------------------------------------------------------------- #


def test_pack_with_long_key_cat_is_rejected() -> None:
    """wiki 的长键（api-testing）混进归档是最容易犯的错 —— 必须被 validate 拦下。"""
    pack = _pack("2026-09-12")
    pack["groups"][0]["questions"][0]["cat"] = "api-testing"
    assert any("cat 非法" in p and "api-testing" in p for p in arc.validate_pack(pack))


def test_site_cats_covers_front_end_vocabulary() -> None:
    """SITE_CATS 必须与前端 CAT_DICT 的键一致 —— 漏一个，那个分类的标签就会掉成兜底样式。"""
    html_text = (SITE_DIR / "index.html").read_text(encoding="utf-8")
    block = re.search(r"const CAT_DICT\s*=\s*\{(.*?)\n\};", html_text, re.DOTALL)
    assert block, "index.html 里找不到 CAT_DICT"
    front_keys = set(re.findall(r'^\s*"?([A-Za-z0-9_-]+)"?\s*:\s*\{', block.group(1), re.MULTILINE))
    assert front_keys == set(arc.SITE_CATS), (
        f"前端 CAT_DICT 与 archive.SITE_CATS 不一致："
        f"前端多 {sorted(front_keys - set(arc.SITE_CATS))}，"
        f"归档多 {sorted(set(arc.SITE_CATS) - front_keys)}"
    )


def test_pitfalls_may_omit_cat() -> None:
    """坑点卡片不展示分类标签，所以允许没有 cat —— 这是刻意豁免，别当成缺失去修。"""
    pack = _pack("2026-09-12")
    assert arc.validate_pack(pack) == []   # _pack 造的坑点本就没有 cat


# --------------------------------------------------------------------------- #
# 2. GitHub 链接白名单
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("url", [
    "https://github.com/microsoft/playwright",
    "https://github.com/microsoft/playwright/",
])
def test_safe_repo_url_accepts_github(url: str) -> None:
    assert arc.SAFE_URL_RE.match(url)


@pytest.mark.parametrize("url", [
    "javascript:alert(1)",
    "data:text/html;base64,PHNjcmlwdD4=",
    "https://evil.com/microsoft/playwright",
    "http://github.com/a/b",
    "https://github.com/../../etc/passwd",
    "https://github.com/a/b?x=1",
])
def test_safe_repo_url_rejects_others(url: str) -> None:
    """榜单数据来自外部采集 + 模型整理，一条 javascript: 就是一次真实注入。"""
    assert not arc.SAFE_URL_RE.match(url)


def test_pack_with_injected_url_is_rejected() -> None:
    pack = _pack("2026-09-12")
    pack["github"]["tools"][0]["url"] = "javascript:alert(1)"
    assert any("非法链接" in p for p in arc.validate_pack(pack))


def test_github_item_without_name_is_rejected() -> None:
    pack = _pack("2026-09-12")
    pack["github"]["skills"][0]["name"] = ""
    assert any("缺少 name" in p for p in arc.validate_pack(pack))


# --------------------------------------------------------------------------- #
# 2c. GitHub 榜单的字段语言契约
#     name 保留英文全名（唯一标识，翻译会丢可检索性）
#     desc 必须是中文（卡片上的介绍描述）
#     descEn 留英文原文（核对译文、重译都靠它）
# --------------------------------------------------------------------------- #


def test_github_desc_must_be_chinese() -> None:
    """英文简介原样上卡片 = 用户看到一屏英文。采集脚本给不出译文，所以必须在
    validate 这一层拦住，而不是等用户发现。"""
    pack = _pack("2026-09-12")
    en = "Playwright is a framework for Web Testing and Automation."
    pack["github"]["skills"][0]["desc"] = en
    pack["github"]["skills"][0]["descEn"] = en
    assert any("未中文化" in p for p in arc.validate_pack(pack))


def test_github_item_with_empty_desc_is_rejected() -> None:
    """接口没返回简介时 desc 会是空串 —— 也要报出来，免得卡片上凭空少一行。"""
    pack = _pack("2026-09-12")
    pack["github"]["projects"][0]["desc"] = ""
    assert any("desc 为空" in p for p in arc.validate_pack(pack))


def test_github_item_without_desc_en_is_rejected() -> None:
    """英文原文必须留档：删掉它就没法核对译文，也没法在改口径后重译。"""
    pack = _pack("2026-09-12")
    pack["github"]["tools"][0].pop("descEn")
    assert any("descEn" in p for p in arc.validate_pack(pack))


def test_normalize_github_item_keeps_english_name_and_raw_desc() -> None:
    """采集阶段的产出形态：name 是英文全名，desc 还是英文原文占位（待译写）。"""
    item = arc.normalize_github_item({
        "full_name": "microsoft/playwright",
        "html_url": "https://github.com/microsoft/playwright",
        "stargazers_count": 96013,
        "description": "Playwright is a framework for Web Testing and Automation.",
        "language": "TypeScript",
        "topics": ["browser", "testing"],
    })
    assert item["name"] == "microsoft/playwright"   # 名称保留英文，不翻译
    assert item["desc"] == item["descEn"]            # 采集时 desc 是英文占位
    assert not arc.has_cjk(item["desc"])             # 所以它一定会被 validate 拦下
    assert "浏览器自动化" in item["scene"]            # scene 由 topics 规则生成，已是中文


@pytest.mark.parametrize("text,expected", [
    ("适合用于接口测试。", True),
    ("Playwright is a framework", False),
    ("", False),
])
def test_has_cjk(text: str, expected: bool) -> None:
    assert arc.has_cjk(text) is expected


# --------------------------------------------------------------------------- #
# 3. 索引一致性与按月合并
# --------------------------------------------------------------------------- #


def test_upsert_day_writes_file_and_index(tmp_arch: Path) -> None:
    fname = arc.upsert_day(_pack("2026-09-12"), archive_dir=tmp_arch)
    assert fname == "2026-09-12.json"
    assert (tmp_arch / fname).exists()

    idx = arc.read_index(tmp_arch)
    assert idx["latest"] == "2026-09-12"
    assert idx["days"][0]["file"] == "2026-09-12.json"
    assert idx["days"][0]["counts"]["questions"] == arc.GROUP_MIN["questions"] * arc.GROUP_COUNT
    assert idx["totalCounts"]["github"] == arc.GITHUB_MIN * len(arc.GITHUB_SECTIONS)


def test_upsert_same_day_twice_keeps_single_index_entry(tmp_arch: Path) -> None:
    arc.upsert_day(_pack("2026-09-12"), archive_dir=tmp_arch)
    arc.upsert_day(_pack("2026-09-12", pad=1), archive_dir=tmp_arch)
    idx = arc.read_index(tmp_arch)
    assert len(idx["days"]) == 1
    # 后写的版本覆盖前一个
    pack = json.loads((tmp_arch / "2026-09-12.json").read_text(encoding="utf-8"))
    assert len(pack["groups"][0]["questions"]) == arc.GROUP_MIN["questions"] + 1


def test_archive_validates_clean_after_upsert(tmp_arch: Path) -> None:
    for d in ("2026-09-10", "2026-09-11", "2026-09-12"):
        arc.upsert_day(_pack(d), archive_dir=tmp_arch)
    assert arc.validate_archive(archive_dir=tmp_arch) == []


def test_rollup_merges_past_month_and_repoints_index(tmp_arch: Path) -> None:
    """跨月合并：日文件消失、月文件出现，且索引里的 file 指向必须跟着改。

    这条是本模块存在的核心理由 —— 索引不改指向，前端在合并当天会全线 404。
    """
    arc.upsert_day(_pack("2026-08-30"), archive_dir=tmp_arch)
    arc.upsert_day(_pack("2026-08-31"), archive_dir=tmp_arch)
    arc.upsert_day(_pack("2026-09-01"), archive_dir=tmp_arch)

    actions = arc.rollup(archive_dir=tmp_arch, keep_month="2026-09")
    assert actions and "2026-08" in actions[0]

    assert not (tmp_arch / "2026-08-30.json").exists()
    assert not (tmp_arch / "2026-08-31.json").exists()
    assert (tmp_arch / "2026-08.json").exists()
    assert (tmp_arch / "2026-09-01.json").exists()   # 当月不合并

    idx = arc.read_index(tmp_arch)
    files = {e["date"]: e["file"] for e in idx["days"]}
    assert files["2026-08-30"] == "2026-08.json"
    assert files["2026-08-31"] == "2026-08.json"
    assert files["2026-09-01"] == "2026-09-01.json"

    assert arc.validate_archive(archive_dir=tmp_arch) == []


def test_rollup_is_idempotent(tmp_arch: Path) -> None:
    """第二次跑合并不该再产生动作 —— 日文件已经不存在了。"""
    arc.upsert_day(_pack("2026-08-31"), archive_dir=tmp_arch)
    assert arc.rollup(archive_dir=tmp_arch, keep_month="2026-09")
    assert arc.rollup(archive_dir=tmp_arch, keep_month="2026-09") == []


def test_rollup_dry_run_changes_nothing(tmp_arch: Path) -> None:
    arc.upsert_day(_pack("2026-08-31"), archive_dir=tmp_arch)
    actions = arc.rollup(archive_dir=tmp_arch, keep_month="2026-09", dry_run=True)
    assert actions
    assert (tmp_arch / "2026-08-31.json").exists()
    assert not (tmp_arch / "2026-08.json").exists()


def test_validate_detects_index_pointing_at_missing_file(tmp_arch: Path) -> None:
    arc.upsert_day(_pack("2026-09-12"), archive_dir=tmp_arch)
    (tmp_arch / "2026-09-12.json").unlink()
    problems = arc.validate_archive(archive_dir=tmp_arch)
    assert any("不存在" in p for p in problems)


def test_validate_detects_unindexed_file_on_disk(tmp_arch: Path) -> None:
    arc.upsert_day(_pack("2026-09-12"), archive_dir=tmp_arch)
    arc.write_json(tmp_arch / "2026-09-11.json", _pack("2026-09-11"))
    problems = arc.validate_archive(archive_dir=tmp_arch)
    assert any("未登记进索引" in p for p in problems)


def test_validate_empty_index_is_reported(tmp_arch: Path) -> None:
    assert arc.validate_archive(archive_dir=tmp_arch)


# --------------------------------------------------------------------------- #
# 4. 分组分布与工具函数
# --------------------------------------------------------------------------- #


def test_split_evenly_spreads_categories() -> None:
    """同类内容不能被整堆摊进同一组 —— 否则会出现「第 2 组全是性能题」。"""
    items = [{"cat": "perf" if i < 9 else "theory", "n": i} for i in range(18)]
    buckets = arc.split_evenly(items, 3)
    assert [len(b) for b in buckets] == [6, 6, 6]
    for b in buckets:
        cats = {x["cat"] for x in b}
        assert cats == {"perf", "theory"}, f"分类未打散：{cats}"


def test_split_evenly_handles_empty_and_uneven() -> None:
    assert arc.split_evenly([], 3) == [[], [], []]
    buckets = arc.split_evenly([{"cat": "a"} for _ in range(7)], 3)
    assert [len(b) for b in buckets] == [3, 2, 2]


def test_build_pack_produces_contract_compliant_pack() -> None:
    flat = {
        "questions": [{"cat": "theory", "q": f"q{i}", "a": "a"} for i in range(40)],
        "knowledge": [{"cat": "theory", "t": f"k{i}", "body": "b"} for i in range(20)],
        "skills": [{"cat": "auto", "t": f"s{i}"} for i in range(18)],
        "pitfalls": [{"t": f"p{i}"} for i in range(18)],
        "exam": [{"cat": "theory", "q": f"e{i}", "o": ["A", "B", "C", "D"], "a": 0} for i in range(30)],
    }
    github = {sec: [_gh_item(i, sec) for i in range(arc.GITHUB_MIN)]
              for sec in arc.GITHUB_SECTIONS}
    pack = arc.build_pack("2026-09-12", flat, github)

    assert pack["groupCount"] == arc.GROUP_COUNT
    assert arc.validate_pack(pack) == []
    # 分堆不能丢条目
    for key in arc.GROUP_MIN:
        assert sum(len(g[key]) for g in pack["groups"]) == len(flat[key])


def test_github_scene_uses_exact_topic_match() -> None:
    """子串匹配会让 topic `ci` 命中 `special`，给无关项目错标「持续集成」。"""
    import seed_archive as seed
    scene = seed.arc.github_scene({"topics": ["special"], "language": "Rust"})
    assert "持续集成" not in scene

    scene2 = seed.arc.github_scene({"topics": ["ci"], "language": "Go"})
    assert "持续集成" in scene2


def test_index_entry_counts_match_pack() -> None:
    pack = _pack("2026-09-12")
    entry = arc.index_entry(pack, "2026-09-12.json")
    assert entry["date"] == "2026-09-12"
    assert entry["groupCount"] == arc.GROUP_COUNT
    assert entry["counts"]["exam"] == arc.GROUP_MIN["exam"] * arc.GROUP_COUNT
    assert entry["counts"]["github"] == arc.GITHUB_MIN * len(arc.GITHUB_SECTIONS)


# --------------------------------------------------------------------------- #
# 5. 真实仓库断言
# --------------------------------------------------------------------------- #


def test_real_repo_archive_is_contract_compliant() -> None:
    """线上实际会被下载的归档，必须通过整套契约校验。"""
    problems = arc.validate_archive()
    assert problems == [], "真实归档存在问题：\n" + "\n".join(problems)


def test_real_repo_index_has_latest_day() -> None:
    idx = arc.read_index()
    assert idx.get("days"), "索引为空 —— 站点启动会直接降级到兜底内容"
    assert idx.get("latest"), "索引缺少 latest 字段"
