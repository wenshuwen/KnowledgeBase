#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把平铺的旧内容包迁移成「按日 × 按组」的归档结构，并采集 GitHub 热点。

**GitHub 采集部分是可复用的**：日常任务不必自己手搓检索语句与限流处理，
直接跑 `--github-only --out <文件>` 拿到四个板块的数据即可 ——
口径、限速、过滤规则都收敛在本文件里，改一次处处一致。

用法：
    # 迁移旧内容包（一次性。旧 content.json 已退役，再跑会提示找不到）
    python seed_archive.py --date 2026-09-12

    # 只采集 GitHub 热点并写出结果（每日任务用这个）
    python seed_archive.py --github-only --out /tmp/gh.json

    # 只统计，不写文件
    python seed_archive.py --dry-run

限流说明：GitHub 未认证搜索 API 约 10 次/分钟，本脚本内置 2.5s 间隔主动限速。
某板块取不满时留空并告警，不阻断整轮（调用方应沿用最近一天归档里的榜单）。

语言契约：脚本只采集不翻译，产出的 `desc` 是英文原文（`descEn` 同样留档）。
调用方拿到结果后必须**逐条把 `desc` 译写成中文简介**，`name` 保留英文全名；
未译写的条目会被 `archive.py validate` 拦下。
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date as Date, timedelta
from pathlib import Path
from typing import Any, Final

sys.path.insert(0, str(Path(__file__).resolve().parent))

import archive as arc  # noqa: E402

SITE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
#: 旧内容包路径。**已退役** —— 仅作一次性迁移来源，日常内容由 site/archive/ 承载
CONTENT_PATH: Final[Path] = SITE_DIR / "content.json"
GH_SEARCH: Final[str] = "https://api.github.com/search/repositories"
UA: Final[str] = "KnowledgeBase-Archive-Seeder/1.0"

#: GitHub 未认证搜索 API 约 10 次/分钟。这里主动限速，宁可慢一点也不撞限流
#: （撞了会整段留空，反而要重跑）。
THROTTLE_SEC: Final[float] = 2.5

log = logging.getLogger("seed_archive")


def fetch_github(query: str, per_page: int = arc.GITHUB_MIN) -> list[dict[str, Any]]:
    """按 stars 降序抓一批仓库。失败时返回空列表并记 warning（不抛异常）。"""
    params = urllib.parse.urlencode(
        {"q": query, "sort": "stars", "order": "desc", "per_page": per_page}
    )
    req = urllib.request.Request(
        f"{GH_SEARCH}?{params}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": UA,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        time.sleep(THROTTLE_SEC)   # 主动限速，避免撞搜索 API 的每分钟限额
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:200]
        except Exception:  # noqa: BLE001
            pass
        log.warning("GitHub 检索失败（HTTP %s）：%s → %s", exc.code, query, body)
        return []
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        log.warning("GitHub 检索异常：%s → %s", query, exc)
        return []

    items = payload.get("items") or []
    log.info("GitHub %-34s 命中 %s 条（总 %s）",
             query, len(items), payload.get("total_count"))
    return [arc.normalize_github_item(it) for it in items]


def dedup(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按仓库全名去重，保持原顺序（榜单已按 stars 降序）。"""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for it in items:
        name = it.get("name") or ""
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(it)
    return out


def collect_section(section: str, since: str) -> list[dict[str, Any]]:
    """采集单个板块，必要时本地过滤 + 放宽检索补足到 GITHUB_MIN 条。"""
    need = arc.GITHUB_MIN
    picked: list[dict[str, Any]] = []

    if section == "skills":
        picked = fetch_github(arc.GITHUB_QUERIES["skills"], per_page=need)

    elif section == "projects":
        picked = fetch_github(arc.GITHUB_QUERIES["projects"].format(since), per_page=need)

    elif section == "testingSkills":
        # 先在 skill 生态里按测试相关 topics 过滤，不够再放宽检索补足
        pool = fetch_github("topic:claude-skills", per_page=40)
        picked = [r for r in pool if arc.matches_any(r, arc.TESTING_HINTS)]
        for extra_query in ("topic:claude-skills topic:testing",
                            "testing skill in:name,description"):
            if len(dedup(picked)) >= need:
                break
            picked += fetch_github(extra_query, per_page=30)

    elif section == "tools":
        # 测试工具：要求命中工具类关键词，且排除 awesome/教程/面试题库这类清单
        pool = fetch_github("topic:testing", per_page=40)
        picked = [
            r for r in pool
            if arc.matches_any(r, arc.TOOL_HINTS) and arc.matches_none(r, arc.NOT_TOOL_HINTS)
        ]
        for extra_query in ("topic:test-automation",
                            "test automation in:name,description"):
            if len(dedup(picked)) >= need:
                break
            picked += fetch_github(extra_query, per_page=30)

    else:
        raise ValueError(f"未知板块：{section}")

    final = dedup(picked)[:need]
    if len(final) < need:
        log.warning("板块 %s 仅取到 %d 条（目标 %d）—— 已尽力放宽检索",
                    section, len(final), need)
    return final


def collect_github() -> dict[str, list[dict[str, Any]]]:
    """采集四个板块。任一板块失败只留空，不阻断其它板块。"""
    since = (Date.today() - timedelta(days=90)).isoformat()
    out: dict[str, list[dict[str, Any]]] = {}
    for section in arc.GITHUB_SECTIONS:
        try:
            out[section] = collect_section(section, since)
        except Exception as exc:  # noqa: BLE001 —— 单个板块失败不影响其余
            log.warning("板块 %s 采集失败，留空：%s", section, exc)
            out[section] = []
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="迁移旧内容包为按日归档结构 / 采集 GitHub 热点")
    parser.add_argument("--date", default=Date.today().isoformat(),
                        help="日包日期（YYYY-MM-DD），默认今天")
    parser.add_argument("--skip-github", action="store_true", help="不抓 GitHub 热点")
    parser.add_argument("--github-only", action="store_true",
                        help="只采集 GitHub 四个板块，不迁移旧内容包（desc 为英文原文，需调用方译写为中文）")
    parser.add_argument("--out", default="", help="配合 --github-only：把结果写到该文件")
    parser.add_argument("--dry-run", action="store_true", help="只统计，不写文件")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        # ---------- 只采集 GitHub：给每日任务复用的入口 ----------
        if args.github_only:
            github = collect_github()
            shortfalls = [s for s in arc.GITHUB_SECTIONS if len(github[s]) < arc.GITHUB_MIN]
            if args.out:
                arc.write_json(Path(args.out), github)
                log.info("已写出 GitHub 榜单：%s", args.out)
            else:
                log.info("%s", json.dumps(github, ensure_ascii=False)[:400])
            for sec in arc.GITHUB_SECTIONS:
                log.info("  %-14s %d 条", sec, len(github[sec]))
            # 采集只做「拿到数据」，不做「翻译」——脚本不调模型。译文由调用方
            # （每日任务）逐条译写覆盖 desc，英文原文已在 descEn 里留档。
            log.warning(
                "⚠ 以上 desc 是 GitHub 接口返回的英文原文（同时存进 descEn）。"
                "写入日包前必须逐条把 desc 译写成中文简介；name 保留英文全名不动。"
                "漏译的条目会被 archive.py validate 拦下"
            )
            if shortfalls:
                log.warning("以下板块未达 %d 条：%s —— 调用方应沿用最近一天归档里的榜单",
                            arc.GITHUB_MIN, ", ".join(shortfalls))
                return 2
            return 0

        # ---------- 迁移旧内容包 ----------
        if not CONTENT_PATH.exists():
            log.error("找不到旧内容包：%s（该文件已退役；日常内容请走 archive.py 的 API）",
                      CONTENT_PATH)
            return 1
        data = arc.load_json(CONTENT_PATH)
        flat = data.get("data") or {}
        for key in arc.GROUP_MIN:
            log.info("旧内容包 %-10s %d 条", key, len(flat.get(key) or []))

        github = arc.empty_github() if args.skip_github else collect_github()
        pack = arc.build_pack(args.date, flat, github)

        problems = arc.validate_pack(pack)
        if problems:
            log.warning("日包未达契约（%d 处）：", len(problems))
            for p in problems:
                log.warning("  · %s", p)
        else:
            log.info("日包通过结构契约校验")

        if args.dry_run:
            log.info("dry-run，未写入文件")
            return 0

        fname = arc.upsert_day(pack)
        log.info("已写入 archive/%s 并更新索引", fname)
        for i, g in enumerate(pack["groups"]):
            log.info("  第 %d 组：题 %d / 知识 %d / 技能 %d / 坑 %d / 考 %d",
                     i + 1, len(g["questions"]), len(g["knowledge"]),
                     len(g["skills"]), len(g["pitfalls"]), len(g["exam"]))
        for sec in arc.GITHUB_SECTIONS:
            log.info("  GitHub %-14s %d 条", sec, len(pack["github"][sec]))
        return 0
    except Exception as exc:  # noqa: BLE001
        log.exception("执行失败：%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
