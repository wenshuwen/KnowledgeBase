#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""归档数据层的读写与维护工具。

站点内容按「日期 × 组」组织：每一天一个包，包内含 N 组内容（每组条数有下限），
外加当天的 GitHub 热点榜单。这样「刷新内容」只是在本地的组之间切换，
「日期检索」则是切到另一天的包。

目录约定（全部位于 site/archive/）：

    site/archive/index.json         索引：可用日期 → 所在文件名（唯一入口）
    site/archive/2026-09-12.json    当月：一天一个文件，文件内容就是那个日包
    site/archive/2026-08.json       跨月后：上月各日合并成一个文件
                                    {month, days: {"2026-08-31": <日包>, ...}}

**为什么索引要记「日期 → 文件名」而不是让前端自己拼路径**：
跨月合并后，同一天的所在文件会从 `2026-08-31.json` 变成 `2026-08.json`。
前端只读索引、不去猜文件名，归档策略将来再怎么变都不需要改前端。

保留策略：**当月按日保留，跨月合并为月文件**（体积收敛，历史可永久检索）。
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import date as Date, datetime
from pathlib import Path
from typing import Any, Final, Iterable

log = logging.getLogger("archive")

ARCHIVE_DIR: Final[Path] = Path(__file__).resolve().parent.parent / "archive"
INDEX_NAME: Final[str] = "index.json"

#: 每天固定组数
GROUP_COUNT: Final[int] = 3

#: 每组各模块的条数下限 —— 自动化生成内容与测试都以此为准。
#: 合起来即每天的下限：题 36 / 知识 18 / 技能 15 / 坑 15 / 考 30 = 114 条。
#: （技能与坑点定 5 而不是 6，是因为迁移前的存量只有 16 / 17 条，撑不满 3×6；
#:  这项属于「有存量支撑的下限」，不是随手取整。）
GROUP_MIN: Final[dict[str, int]] = {
    "questions": 12,
    "knowledge": 6,
    "skills": 5,
    "pitfalls": 5,
    "exam": 10,
}

#: GitHub 热点的四个板块（按「天」不按「组」——它是当日排行榜快照）
GITHUB_SECTIONS: Final[tuple[str, ...]] = ("skills", "projects", "testingSkills", "tools")

#: 每个板块至少展示的条数
GITHUB_MIN: Final[int] = 10

#: 链接只允许指向 GitHub 仓库页，防止内容里混进 javascript: / data: 之类的注入
SAFE_URL_RE: Final[re.Pattern[str]] = re.compile(
    r"^https://github\.com/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+/?$"
)

DATE_RE: Final[re.Pattern[str]] = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# --------------------------------------------------------------------------- #
# 基础读写
# --------------------------------------------------------------------------- #


def load_json(path: Path) -> Any:
    """读取 JSON；失败抛异常（调用方决定是降级还是中断）。"""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    """写 JSON。缩进 1，与站点其它产物保持一致。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


def day_file(date_str: str) -> Path:
    return ARCHIVE_DIR / f"{date_str}.json"


def month_file(month_str: str) -> Path:
    return ARCHIVE_DIR / f"{month_str}.json"


def month_of(date_str: str) -> str:
    """`2026-09-12` → `2026-09`"""
    return date_str[:7]


def read_index(archive_dir: Path | None = None) -> dict[str, Any]:
    """读索引。不存在时返回一个空骨架。"""
    path = (archive_dir or ARCHIVE_DIR) / INDEX_NAME
    if not path.exists():
        return {"version": "", "updatedAt": "", "latest": "", "days": []}
    return load_json(path)


def write_index(index: dict[str, Any], archive_dir: Path | None = None) -> None:
    """写索引，并顺带刷新汇总字段（条数、天数、最新日期）。"""
    days = index.get("days") or []
    days.sort(key=lambda d: str(d.get("date", "")))
    index["days"] = days

    if days:
        index["latest"] = days[-1]["date"]
        index["version"] = days[-1]["date"]
    index["updatedAt"] = Date.today().isoformat()
    index["dayCount"] = len(days)

    counts: dict[str, int] = {k: 0 for k in (*GROUP_MIN, "github")}
    for d in days:
        c = d.get("counts") or {}
        for k in counts:
            counts[k] += int(c.get(k) or 0)
    index["totalCounts"] = counts

    write_json((archive_dir or ARCHIVE_DIR) / INDEX_NAME, index)


def index_entry(pack: dict[str, Any], file_name: str) -> dict[str, Any]:
    """由日包生成索引条目。"""
    groups = pack.get("groups") or []
    counts = {k: sum(len(g.get(k) or []) for g in groups) for k in GROUP_MIN}
    counts["github"] = sum(len((pack.get("github") or {}).get(s) or []) for s in GITHUB_SECTIONS)
    return {
        "date": pack.get("date"),
        "file": file_name,
        "groupCount": len(groups),
        "counts": counts,
    }


# --------------------------------------------------------------------------- #
# 写入与合并
# --------------------------------------------------------------------------- #


def upsert_day(pack: dict[str, Any], *, archive_dir: Path | None = None) -> str:
    """写入某一天的日包并更新索引，返回写入的文件名。

    当月写 `YYYY-MM-DD.json`；若该日已落在历史月文件里，则就地更新月文件内的对应日。
    """
    base = archive_dir or ARCHIVE_DIR
    d = str(pack.get("date") or "")
    if not DATE_RE.match(d):
        raise ValueError(f"日包的 date 非法：{d!r}（应为 YYYY-MM-DD）")

    base.mkdir(parents=True, exist_ok=True)
    index = read_index(base)

    existing = next((e for e in index.get("days") or [] if e.get("date") == d), None)
    target_name = (existing or {}).get("file") or f"{d}.json"

    if target_name == f"{d}.json":
        write_json(base / target_name, pack)
    else:
        # 该日已被合并进月文件 → 只更新月文件里的那一天，不拆回去
        mpath = base / target_name
        mdata = load_json(mpath)
        mdata.setdefault("days", {})[d] = pack
        write_json(mpath, mdata)

    entry = index_entry(pack, target_name)
    days = [e for e in (index.get("days") or []) if e.get("date") != d]
    days.append(entry)
    index["days"] = days
    write_index(index, base)
    return target_name


def rollup(*, archive_dir: Path | None = None, keep_month: str | None = None,
           dry_run: bool = False) -> list[str]:
    """把「非当月」的按日文件合并成月文件，并删除已合并的日文件。

    `keep_month` 默认取本月（YYYY-MM）。返回本次合并动作的描述列表。
    幂等：已合并过的月文件不会被重复处理（对应的日文件已不存在）。
    """
    base = archive_dir or ARCHIVE_DIR
    keep = keep_month or Date.today().strftime("%Y-%m")

    # 收集可合并的按日文件：文件名形如 YYYY-MM-DD.json，且月份早于 keep
    candidates = sorted(
        p for p in base.glob("*.json")
        if DATE_RE.match(p.stem) and p.stem[:7] < keep
    )
    if not candidates:
        return []

    by_month: dict[str, list[Path]] = {}
    for p in candidates:
        by_month.setdefault(p.stem[:7], []).append(p)

    actions: list[str] = []
    for month, paths in sorted(by_month.items()):
        mpath = base / f"{month}.json"
        merged: dict[str, Any] = (
            load_json(mpath) if mpath.exists() else {"month": month, "days": {}}
        )
        merged["month"] = month
        merged.setdefault("days", {})

        for p in paths:
            merged["days"][p.stem] = load_json(p)
        merged["days"] = dict(sorted(merged["days"].items()))
        merged["dayCount"] = len(merged["days"])

        actions.append(f"{month}：合并 {len(paths)} 个日文件 → {mpath.name}（共 {merged['dayCount']} 天）")
        if dry_run:
            continue

        write_json(mpath, merged)
        for p in paths:
            p.unlink()
            log.info("已合并并删除：%s", p.name)

    if not dry_run:
        # 索引里的文件指向要跟着改
        index = read_index(base)
        for entry in index.get("days") or []:
            d = str(entry.get("date") or "")
            if DATE_RE.match(d) and month_of(d) < keep:
                entry["file"] = f"{month_of(d)}.json"
        write_index(index, base)

    return actions


# --------------------------------------------------------------------------- #
# 校验（供测试与自动化自检使用）
# --------------------------------------------------------------------------- #


def validate_pack(pack: dict[str, Any]) -> list[str]:
    """校验单个日包是否满足结构契约。返回问题列表，空表示通过。"""
    problems: list[str] = []

    d = pack.get("date")
    if not isinstance(d, str) or not DATE_RE.match(d):
        problems.append(f"date 缺失或格式非法：{d!r}")
    elif d in ("0000-00-00",):
        problems.append("date 非法日期")

    groups = pack.get("groups")
    if not isinstance(groups, list) or not groups:
        problems.append("groups 缺失或为空")
        return problems

    if len(groups) < GROUP_COUNT:
        problems.append(f"组数不足：{len(groups)} < {GROUP_COUNT}")

    for gi, g in enumerate(groups):
        if not isinstance(g, dict):
            problems.append(f"第 {gi} 组不是对象")
            continue
        for key, minimum in GROUP_MIN.items():
            items = g.get(key)
            if not isinstance(items, list):
                problems.append(f"第 {gi} 组缺少 {key} 数组")
            elif len(items) < minimum:
                problems.append(f"第 {gi} 组 {key} 条数不足：{len(items)} < {minimum}")

    gh = pack.get("github")
    if not isinstance(gh, dict):
        problems.append("github 板块缺失")
    else:
        for sec in GITHUB_SECTIONS:
            items = gh.get(sec)
            if not isinstance(items, list):
                problems.append(f"github.{sec} 缺失")
            elif len(items) < GITHUB_MIN:
                problems.append(f"github.{sec} 条数不足：{len(items)} < {GITHUB_MIN}")
            else:
                for it in items:
                    url = (it or {}).get("url")
                    if not isinstance(url, str) or not SAFE_URL_RE.match(url):
                        problems.append(f"github.{sec} 存在非法链接：{url!r}")
                    if not (it or {}).get("name"):
                        problems.append(f"github.{sec} 有条目缺少 name")

    return problems


def validate_archive(*, archive_dir: Path | None = None,
                     strict_counts: bool = True) -> list[str]:
    """校验整个归档目录：索引 ↔ 文件双向一致、日包结构合法。"""
    base = archive_dir or ARCHIVE_DIR
    problems: list[str] = []

    index = read_index(base)
    days = index.get("days") or []
    if not days:
        return [f"索引为空或不存在：{base / INDEX_NAME}"]

    seen_dates: set[str] = set()
    for entry in days:
        d = str(entry.get("date") or "")
        fname = str(entry.get("file") or "")
        if not DATE_RE.match(d):
            problems.append(f"索引条目日期非法：{d!r}")
            continue
        if d in seen_dates:
            problems.append(f"索引日期重复：{d}")
        seen_dates.add(d)

        fpath = base / fname
        if not fpath.exists():
            problems.append(f"{d} 指向的文件不存在：{fname}")
            continue

        if fname == f"{d}.json":
            pack = load_json(fpath)
        else:
            month_days = (load_json(fpath) or {}).get("days") or {}
            pack = month_days.get(d)
            if pack is None:
                problems.append(f"月文件 {fname} 中缺少 {d}")
                continue

        if strict_counts:
            for p in validate_pack(pack):
                problems.append(f"[{d}] {p}")

    # 反向：磁盘上存在但索引没登记的日/月文件
    for p in sorted(base.glob("*.json")):
        if p.name == INDEX_NAME:
            continue
        if DATE_RE.match(p.stem) and p.stem not in seen_dates:
            problems.append(f"磁盘上的日文件未登记进索引：{p.name}")
        elif re.match(r"^\d{4}-\d{2}$", p.stem):
            month_days = (load_json(p) or {}).get("days") or {}
            for d in month_days:
                if d not in seen_dates:
                    problems.append(f"月文件 {p.name} 中的 {d} 未登记进索引")

    return problems


# --------------------------------------------------------------------------- #
# GitHub 热点采集
# --------------------------------------------------------------------------- #

#: 四个板块的检索口径 —— 按 GitHub topics 区分，同类内按 stars 降序
GITHUB_QUERIES: Final[dict[str, str]] = {
    # 热门 skill：面向 AI Agent 的 skill / 插件生态
    "skills": "topic:claude-skills",
    # 热门项目：高星且近期仍活跃（避免榜单常年不变）
    "projects": "stars:>20000 pushed:>{}",
    # 热门测试辅助 skill：skill 生态里与测试相关的
    "testingSkills": "topic:claude-skills testing",
    # 热门测试工具：测试领域的工具类仓库
    "tools": "topic:testing",
}

#: 由 GitHub topics / 语言推导「使用场景」的规则表。
#: 不做自由发挥 —— 只用可核实的 topics 信息拼一句场景，避免编造项目能力。
SCENE_RULES: Final[tuple[tuple[str, str], ...]] = (
    ("e2e", "端到端测试"),
    ("browser", "浏览器自动化"),
    ("playwright", "浏览器自动化"),
    ("selenium", "浏览器自动化"),
    ("api", "接口测试"),
    ("rest", "接口测试"),
    ("graphql", "接口测试"),
    ("load-testing", "性能压测"),
    ("performance", "性能压测"),
    ("benchmark", "性能基准"),
    ("k6", "性能压测"),
    ("jmeter", "性能压测"),
    ("security", "安全测试"),
    ("penetration", "安全测试"),
    ("fuzzing", "模糊测试"),
    ("mock", "依赖打桩"),
    ("stub", "依赖打桩"),
    ("contract", "契约测试"),
    ("test-automation", "自动化用例编排"),
    ("testing", "测试工程"),
    ("qa", "测试工程"),
    ("ci", "持续集成"),
    ("claude", "AI Agent 能力扩展"),
    ("mcp", "AI Agent 工具接入"),
    ("llm", "大模型工程"),
    ("agent", "AI Agent 构建"),
    ("skill", "AI Agent 能力扩展"),
    ("observability", "可观测性"),
    ("monitoring", "线上监控"),
    ("lint", "静态检查"),
)


def github_scene(repo: dict[str, Any]) -> str:
    """由 topics / 语言推导一句「使用场景」。

    刻意保守：只依据仓库自报的 topics 组合出场景短语，不推测具体功能，
    因此可能出现「场景偏泛」而不可能「场景编造」。

    topics 用**精确匹配**而不是子串匹配 —— 早先用子串时，
    规则里的 `ci` 会命中 `special` / `efficiency` 这类 topic，
    给「从零造轮子」这种项目标上「持续集成」，属于明显错标。
    """
    topics = {str(t).lower() for t in (repo.get("topics") or [])}
    hits: list[str] = []
    for key, phrase in SCENE_RULES:
        if phrase in hits:
            continue
        if key in topics:
            hits.append(phrase)
        if len(hits) >= 3:
            break

    lang = repo.get("language") or ""
    if hits:
        scene = "、".join(hits)
        # 文案里不再带「场景」二字 —— 卡片上的标签已经写着「使用场景：」，
        # 生成句再重复一次会读成「使用场景：适合接口测试场景」。
        return f"适合用于{scene}；主语言 {lang}。" if lang else f"适合用于{scene}。"
    if lang:
        return f"通用工程库，主语言 {lang}；可用于日常开发与测试辅助。"
    return "通用工程库，可用于日常开发与测试辅助。"


#: 判定「与测试相关」的关键词（用于 testingSkills 板块的本地过滤）
TESTING_HINTS: Final[tuple[str, ...]] = (
    "test", "testing", "qa", "e2e", "quality", "selenium", "playwright", "cypress",
    "jest", "vitest", "pytest", "junit", "appium", "k6", "jmeter", "postman",
    "fuzz", "mutation", "contract", "coverage", "bug", "assert",
)

#: 判定「工具类」的关键词（用于 tools 板块的本地过滤）
TOOL_HINTS: Final[tuple[str, ...]] = (
    "test-automation", "e2e", "selenium", "playwright", "cypress", "appium",
    "load-testing", "performance", "api-testing", "testing", "pytest", "jest",
    "vitest", "junit", "k6", "jmeter", "postman", "bruno", "insomnia", "allure",
    "fuzz", "mock", "docker", "cli",
)

#: 明显「不是工具」的仓库特征 —— 清单、教程、面试题库、路线图都排除掉
NOT_TOOL_HINTS: Final[tuple[str, ...]] = (
    "awesome", "awesome-list", "interview", "tutorial", "roadmap", "books",
    "cheatsheet", "free-programming", "best-practices", "curated-list",
)


def repo_text(repo: dict[str, Any]) -> str:
    """把仓库的可检索文本拼起来（名称 + 简介 + topics + 语言），统一小写。"""
    parts = [
        str(repo.get("name") or ""),
        str(repo.get("description") or ""),
        str(repo.get("language") or ""),
        " ".join(str(t) for t in (repo.get("topics") or [])),
    ]
    return " ".join(parts).lower()


def matches_any(repo: dict[str, Any], hints: tuple[str, ...]) -> bool:
    """仓库文本是否命中任一关键词。"""
    text = repo_text(repo)
    return any(h in text for h in hints)


def matches_none(repo: dict[str, Any], hints: tuple[str, ...]) -> bool:
    """仓库文本是否完全不命中关键词（用于排除清单/教程类）。"""
    return not matches_any(repo, hints)


def normalize_github_item(repo: dict[str, Any]) -> dict[str, Any]:
    """把 GitHub API 的仓库对象裁剪成站点卡片需要的字段。"""
    return {
        "name": repo.get("full_name") or "",
        "url": repo.get("html_url") or "",
        "stars": int(repo.get("stargazers_count") or 0),
        "desc": (repo.get("description") or "").strip(),
        "scene": github_scene(repo),
        "lang": repo.get("language") or "",
        "topics": [str(t) for t in (repo.get("topics") or [])][:8],
    }


def empty_github() -> dict[str, list[dict[str, Any]]]:
    return {sec: [] for sec in GITHUB_SECTIONS}


@dataclass
class Group:
    """一组内容。"""

    questions: list[dict[str, Any]] = field(default_factory=list)
    knowledge: list[dict[str, Any]] = field(default_factory=list)
    skills: list[dict[str, Any]] = field(default_factory=list)
    pitfalls: list[dict[str, Any]] = field(default_factory=list)
    exam: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "questions": self.questions,
            "knowledge": self.knowledge,
            "skills": self.skills,
            "pitfalls": self.pitfalls,
            "exam": self.exam,
        }


def split_evenly(items: Iterable[dict[str, Any]], buckets: int) -> list[list[dict[str, Any]]]:
    """把条目均分到 N 组，并尽量让每组分类分布均衡。

    做法：先按 cat 排序把同类聚在一起，再轮转发牌 —— 同一分类会被摊到不同组，
    避免出现「第 2 组全是性能题」这种分布。
    """
    ordered = sorted(items, key=lambda x: (str(x.get("cat") or ""),))
    out: list[list[dict[str, Any]]] = [[] for _ in range(buckets)]
    for i, item in enumerate(ordered):
        out[i % buckets].append(item)
    return out


def build_pack(date_str: str, data: dict[str, Any],
               github: dict[str, list[dict[str, Any]]] | None = None) -> dict[str, Any]:
    """由平铺的五类内容组装成「一天 × N 组」的日包。"""
    buckets = {k: split_evenly(data.get(k) or [], GROUP_COUNT) for k in GROUP_MIN}
    groups = [
        Group(
            questions=buckets["questions"][i],
            knowledge=buckets["knowledge"][i],
            skills=buckets["skills"][i],
            pitfalls=buckets["pitfalls"][i],
            exam=buckets["exam"][i],
        ).as_dict()
        for i in range(GROUP_COUNT)
    ]
    return {
        "date": date_str,
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "groupCount": GROUP_COUNT,
        "groups": groups,
        "github": github or empty_github(),
    }


# --------------------------------------------------------------------------- #
# 命令行入口
# --------------------------------------------------------------------------- #

#: 命令行里用得到的常量，供自动化任务引用（照着写、不用猜数字）
REQUIREMENTS_HINT: Final[str] = (
    f"每天 {GROUP_COUNT} 组；每组下限 "
    + " / ".join(f"{k} {v}" for k, v in GROUP_MIN.items())
    + f"；GitHub 四板块各 {GITHUB_MIN} 条（{', '.join(GITHUB_SECTIONS)}）"
)


def _cmd_validate(args: argparse.Namespace) -> int:
    problems = validate_archive()
    if problems:
        log.error("归档校验未通过，%d 处问题：", len(problems))
        for p in problems:
            log.error("  · %s", p)
        return 1
    idx = read_index()
    log.info("归档校验通过：%d 天，最新 %s", len(idx.get("days") or []), idx.get("latest"))
    return 0


def _cmd_rollup(args: argparse.Namespace) -> int:
    actions = rollup(dry_run=args.dry_run)
    if not actions:
        log.info("没有需要合并的历史月份")
        return 0
    for a in actions:
        log.info("%s%s", "[dry-run] " if args.dry_run else "", a)
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    idx = read_index()
    days = idx.get("days") or []
    log.info("归档天数：%d", len(days))
    log.info("最新日期：%s", idx.get("latest") or "（无）")
    log.info("契约要求：%s", REQUIREMENTS_HINT)
    for e in days[-5:]:
        c = e.get("counts") or {}
        log.info("  %s → %s | %d 组 | 题 %s / 知识 %s / 技能 %s / 坑 %s / 考 %s / GH %s",
                 e.get("date"), e.get("file"), e.get("groupCount") or 0,
                 c.get("questions", 0), c.get("knowledge", 0), c.get("skills", 0),
                 c.get("pitfalls", 0), c.get("exam", 0), c.get("github", 0))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="归档数据层的维护工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="校验索引与日包是否满足契约")
    p_val.set_defaults(func=_cmd_validate)

    p_roll = sub.add_parser("rollup", help="把非当月的按日文件合并成月文件")
    p_roll.add_argument("--dry-run", action="store_true", help="只报告，不改文件")
    p_roll.set_defaults(func=_cmd_rollup)

    p_st = sub.add_parser("status", help="打印归档概览与契约要求")
    p_st.set_defaults(func=_cmd_status)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        return int(args.func(args))
    except Exception as exc:  # noqa: BLE001
        log.exception("执行失败：%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
