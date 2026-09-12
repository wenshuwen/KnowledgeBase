#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本地知识库编译成面试助手站点可消费的 kb.json。

设计要点（对应 WIKI-SCHEMA.md 第 8 节渲染契约）：
  1. publish: false 的页面必须在本脚本内过滤 —— 前端过滤等同于已公开；
  2. 缺少 interview 块的页面静默跳过（不上站，不算错误）；
  3. interview 块存在但字段非法 → 记入待修清单并跳过，不中断整体构建；
  4. 输出内容哈希进版本号，避免无实质变更时也触发站点更新；内容未变时跳过写入；
  5. 每次构建都检查全库链接网络：死链与孤页必须报出来 ——
     它们不会让构建失败，只会在线上表现为「点进去什么都没有」，不主动报就发现不了；
  6. 代码片段内的 `[[ ]]` 视为示例写法，不参与链接替换；代码内容交给 markdown 正常转义。
     **绝不能用"占位符替换后再还原"的做法** —— 那样 markdown 失去转义机会，
     还原时会把示例里的原始 HTML（img/script）直接注入页面并在浏览器中真实执行；
  7. 产物里出现 script/img 等标签即视为构建失败 —— 本渲染器不会产出这些标签。

用法：
    python build_kb.py              # 正常构建，写入 kb.json
    python build_kb.py --dry-run    # 只校验与统计，不写文件
    python build_kb.py --force      # 内容未变时也强制重写产物
    python build_kb.py -v           # 输出每个页面的处理详情

退出码：0 正常；1 构建异常、存在死链，或产物混入未转义 HTML。
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Final

import markdown
import yaml

# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #

KB_ROOT: Final[Path] = Path("/Users/tigerwen/WorkBuddy/KnowledgeBase")
WIKI_DIR: Final[Path] = KB_ROOT / "wiki"
OUTPUT_PATH: Final[Path] = Path(__file__).resolve().parent / "kb.json"

#: 站点一级分类枚举，与 WIKI-SCHEMA 8.2 保持一致
CAT_LABELS: Final[dict[str, str]] = {
    "theory": "测试理论",
    "api-testing": "接口测试",
    "performance-testing": "性能测试",
    "automation-testing": "自动化测试",
    "security-testing": "安全测试",
    "ai-testing": "AI 测试",
    "ai-agent-testing": "AI Agent 测试",
    "python": "Python 基础",
    "ai-tools": "AI 测试工具",
    "env-setup": "测试环境搭建",
    "database-linux": "数据库/Linux",
    "scenario": "场景题",
    "cicd": "CI/CD",
}

KIND_ENUM: Final[tuple[str, ...]] = ("question", "knowledge", "skill", "pitfall")
LEVEL_ENUM: Final[tuple[str, ...]] = ("初级", "中级", "高级")

#: wiki 根目录下不属于内容页的文件
SKIP_FILENAMES: Final[set[str]] = {"index.md", "log.md"}

FRONTMATTER_RE: Final[re.Pattern[str]] = re.compile(
    r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.DOTALL
)
H1_RE: Final[re.Pattern[str]] = re.compile(r"\A\s*#\s+.+?\r?\n", re.DOTALL)
WIKILINK_RE: Final[re.Pattern[str]] = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]")
IMAGE_RE: Final[re.Pattern[str]] = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

CODE_FENCE_RE: Final[re.Pattern[str]] = re.compile(r"```.*?```", re.DOTALL)
CODE_SPAN_RE: Final[re.Pattern[str]] = re.compile(r"`[^`\n]*`")

#: 渲染产物里绝不允许出现的标签 —— 出现即说明正文里的原始 HTML 没有被转义
UNSAFE_TAGS: Final[tuple[str, ...]] = (
    "<script", "<img", "<iframe", "<form", "<svg", "<object", "<embed", "<link", "<style",
)

#: 一次扫描处理「代码」与「双链」两类片段。代码分支原样返回、交给 markdown 正常转义，
#: 这样既避免代码里的 [[示例]] 被误当链接，又不会破坏代码块自身的转义与 <code> 渲染。
WIKILINK_OR_CODE_RE: Final[re.Pattern[str]] = re.compile(
    r"(?P<code>```[^\n`]*\r?\n.*?```|`[^`\n]*`)"
    r"|\[\[(?P<page>[^\]|]+?)(?:\|(?P<alias>[^\]]+?))?\]\]",
    re.DOTALL,
)

log = logging.getLogger("build_kb")


# --------------------------------------------------------------------------- #
# 双链解析（自动跳过代码片段）
# --------------------------------------------------------------------------- #


def extract_links(markdown_text: str) -> list[str]:
    """提取页面出链，自动忽略代码块与行内代码里的示例写法。"""
    return sorted({
        m.group("page").strip()
        for m in WIKILINK_OR_CODE_RE.finditer(markdown_text)
        if m.group("code") is None
    })


def replace_wikilinks(markdown_text: str) -> str:
    """把 `[[页面名]]` 换成带 data-page 的 span，代码片段原样保留。

    注意：这里**不能**用"整段替换成占位符、事后还原"的做法 ——
    那样 markdown 就没机会对代码内容做转义与 `<code>` 包裹，
    还原时会把原始 HTML（如示例里的 <img>、<script>）直接注入页面。
    """
    def _sub(match: re.Match[str]) -> str:
        if match.group("code") is not None:
            return match.group("code")
        page = match.group("page").strip()
        label = (match.group("alias") or page).strip()
        return (
            f'<span class="wl" data-page="{html.escape(page, quote=True)}">'
            f"{html.escape(label)}</span>"
        )

    return WIKILINK_OR_CODE_RE.sub(_sub, markdown_text)


# --------------------------------------------------------------------------- #
# 数据结构
# --------------------------------------------------------------------------- #


@dataclass
class Issue:
    """一条待修问题。"""

    path: str
    reason: str


@dataclass
class KbPage:
    """一个可上站的知识库页面。"""

    id: str
    title: str
    cat: str
    kind: str
    level: str
    question: str
    domain: str
    updated: str
    confidence: str
    tags: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    body: str = ""
    source_path: str = ""


@dataclass
class BuildResult:
    """一次构建的结果汇总。"""

    pages: list[KbPage] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    unsafe: list[str] = field(default_factory=list)
    scanned: int = 0
    skipped_unpublished: int = 0
    skipped_no_interview: int = 0
    image_refs: int = 0


# --------------------------------------------------------------------------- #
# 解析
# --------------------------------------------------------------------------- #


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """切分 YAML frontmatter 与正文。无 frontmatter 时返回空字典与原文。"""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        log.warning("frontmatter 解析失败，按无 frontmatter 处理：%s", exc)
        return {}, text
    if not isinstance(meta, dict):
        return {}, text
    return meta, text[match.end():]


def render_body(markdown_text: str, title: str) -> str:
    """markdown → HTML，并做站点侧需要的两处规整。

    - 去掉与 title 重复的首个一级标题（卡片本身已展示标题）
    - `[[页面名]]` 转成带 data-page 的 span；代码片段内的保持原样
    """
    body_md = markdown_text
    h1 = H1_RE.match(body_md)
    if h1 and title and title in h1.group(0):
        body_md = body_md[h1.end():]

    return markdown.markdown(
        replace_wikilinks(body_md),
        extensions=["extra", "sane_lists", "toc"],
        output_format="html",
    )


def unsafe_html_in(body_html: str) -> list[str]:
    """检查渲染产物里是否混进了原始 HTML 标签。

    本站的渲染器只会产出 <p>/<ul>/<code>/<pre>/<span class="wl"> 等，
    一旦出现 <script>/<img> 等标签，说明正文里的示例代码没有被转义 ——
    那不只是样式问题，而是会在浏览器里真实执行/发起请求。
    """
    return [tag for tag in UNSAFE_TAGS if tag in body_html.lower()]


def page_id(rel_path: str) -> str:
    """用相对路径生成稳定 id（同名页面在不同目录时不会撞车）。"""
    return rel_path.replace("\\", "/").removesuffix(".md")


def load_page(path: Path, verbose: bool = False) -> tuple[KbPage | None, str | None]:
    """读取单个页面。

    返回值语义：
        (page, None)    —— 成功，可上站
        (None, None)    —— 正常跳过（未发布 / 无 interview 块 / 非内容页）
        (None, reason)  —— 字段非法，需人工修
    """
    rel = str(path.relative_to(KB_ROOT))

    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"读取失败：{exc}"

    meta, body_md = split_frontmatter(raw)

    # 非内容页直接跳过
    if path.name in SKIP_FILENAMES:
        return None, None

    # 未发布：必须在构建期过滤
    if meta.get("publish", True) is False:
        if verbose:
            log.debug("跳过（publish=false）：%s", rel)
        return None, "UNPUBLISHED"

    interview = meta.get("interview")
    if not isinstance(interview, dict) or not interview:
        return None, None  # 不上站，但不是错误

    # ---- 字段校验 ----
    title = str(meta.get("title") or "").strip()
    if not title:
        return None, "缺少 title"

    cat = str(interview.get("cat") or "").strip()
    if cat not in CAT_LABELS:
        return None, f"interview.cat 非法或缺省：{cat!r}（合法值见 WIKI-SCHEMA 8.2）"

    kind = str(interview.get("kind") or "").strip()
    if kind not in KIND_ENUM:
        return None, f"interview.kind 非法或缺省：{kind!r}（合法值：{'/'.join(KIND_ENUM)}）"

    level = str(interview.get("level") or "").strip()
    if level and level not in LEVEL_ENUM:
        log.warning("%s：level 取值异常 %r，按空处理", rel, level)
        level = ""

    question = str(interview.get("q") or "").strip()
    if kind == "question" and not question:
        log.warning("%s：kind=question 但未填 q，站点将回退显示标题", rel)
        question = title

    tags = meta.get("tags") or []
    if not isinstance(tags, list):
        tags = [str(tags)]

    body_html = render_body(body_md, title)
    images = IMAGE_RE.findall(body_md)

    page = KbPage(
        id=page_id(rel),
        title=title,
        cat=cat,
        kind=kind,
        level=level,
        question=question,
        domain=str(meta.get("domain") or ""),
        updated=str(meta.get("updated") or ""),
        confidence=str(meta.get("confidence") or "medium"),
        tags=[str(t) for t in tags],
        links=extract_links(body_md),
        body=body_html,
        source_path=rel,
    )
    if images:
        log.warning("%s：含 %d 处图片引用，站点需另配资源路径", rel, len(images))

    return page, None


def scan_wiki(verbose: bool = False) -> BuildResult:
    """遍历 wiki/ 下所有 markdown，产出可上站页面与待修清单。"""
    result = BuildResult()

    if not WIKI_DIR.is_dir():
        log.error("wiki 目录不存在：%s", WIKI_DIR)
        return result

    for path in sorted(WIKI_DIR.rglob("*.md")):
        result.scanned += 1
        try:
            page, reason = load_page(path, verbose=verbose)
        except Exception as exc:  # noqa: BLE001 —— 单文件异常不阻断整体构建
            log.exception("未预期的解析异常：%s", path)
            result.issues.append(Issue(str(path.relative_to(KB_ROOT)), f"解析异常：{exc}"))
            continue

        if page is not None:
            result.pages.append(page)
            leaked = unsafe_html_in(page.body)
            if leaked:
                result.unsafe.append(
                    f"{page.source_path} —— 含未转义 HTML：{', '.join(leaked)}"
                )
            continue

        if reason == "UNPUBLISHED":
            result.skipped_unpublished += 1
        elif reason is None:
            result.skipped_no_interview += 1
        else:
            result.issues.append(Issue(str(path.relative_to(KB_ROOT)), reason))

    return result


# --------------------------------------------------------------------------- #
# 图谱健康检查
# --------------------------------------------------------------------------- #


@dataclass
class GraphCheck:
    """全库链接网络的检查结果。"""

    total_pages: int = 0
    broken: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)


def check_graph() -> GraphCheck:
    """独立遍历 wiki/，检查死链与孤页。

    为什么独立于 scan_wiki：死链要对着**全部页面**判定，
    而未发布 / 无 interview 块的页面同样可能被链接，不能只看上站页面。

    这两项必须每次构建都跑 —— 它们不会让构建失败，
    只会在线上表现为「点进去什么都没有」，不主动报就永远发现不了。
    """
    result = GraphCheck()

    names: set[str] = set()
    edges: list[tuple[str, str]] = []

    for path in sorted(WIKI_DIR.rglob("*.md")):
        if path.name in SKIP_FILENAMES:
            continue
        names.add(path.stem)
        try:
            _, body = split_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            log.warning("图谱检查跳过 %s：%s", path.name, exc)
            continue
        rel = str(path.relative_to(WIKI_DIR))
        for link in extract_links(body):
            edges.append((rel, link))

    result.total_pages = len(names)

    inbound: dict[str, int] = {n: 0 for n in names}
    for src, link in edges:
        if link in names:
            inbound[link] += 1
        else:
            result.broken.append(f"{src} → [[{link}]]")

    result.orphans = sorted(n for n, c in inbound.items() if c == 0)
    return result


# --------------------------------------------------------------------------- #
# 输出
# --------------------------------------------------------------------------- #


def content_digest(pages: list[KbPage]) -> str:
    """内容指纹：只取决于页面内容，与构建时间无关。

    幂等判据必须是它，而不能是 version —— version 里带日期，跨天必然不同。
    """
    payload = json.dumps(
        [asdict(p) for p in pages],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]


def compute_version(digest: str) -> str:
    """版本号 = 日期 + 内容指纹。日期只供人读，不参与「是否变更」的判定。"""
    return f"kb-{date.today():%Y.%m.%d}-{digest}"


def build_payload(result: BuildResult) -> dict[str, Any]:
    """组装 kb.json 内容。sources 等内部信息不进产物。"""
    pages = sorted(result.pages, key=lambda p: (list(CAT_LABELS).index(p.cat), p.title))

    by_cat: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for p in pages:
        by_cat[p.cat] = by_cat.get(p.cat, 0) + 1
        by_kind[p.kind] = by_kind.get(p.kind, 0) + 1

    digest = content_digest(pages)
    return {
        "contentHash": digest,
        "version": compute_version(digest),
        "updatedAt": date.today().isoformat(),
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "summary": "知识库共 {} 条，覆盖 {} 个分类".format(len(pages), len(by_cat)),
        "stats": {"total": len(pages), "byCat": by_cat, "byKind": by_kind},
        "cats": [
            {"cat": c, "label": label, "count": by_cat.get(c, 0)}
            for c, label in CAT_LABELS.items()
            if by_cat.get(c, 0) > 0
        ],
        "data": {"items": [asdict(p) for p in pages]},
    }


def should_skip_write(payload: dict[str, Any], force: bool = False) -> bool:
    """产物内容未变时跳过写入，保证构建真正幂等。

    判据是 `contentHash`（纯内容指纹），既不是 version 也不是文件整体：
    - `version` 带日期 → 跨天必然不同，会造成「每天一次无意义 diff + 重新部署」
    - `generatedAt` 精确到秒 → 每次构建都不同
    拿易变字段当判据，等于没有幂等；缺 `contentHash` 的旧产物视为已变更（写入一次即迁移）。
    """
    if force or not OUTPUT_PATH.exists():
        return False
    try:
        existing = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(existing.get("contentHash")) and existing.get("contentHash") == payload.get("contentHash")


def report(result: BuildResult, graph: GraphCheck, status: str) -> None:
    """打印构建报告。"""
    log.info("—" * 46)
    log.info("扫描 %d 个文件", result.scanned)
    log.info("可上站 %d 个", len(result.pages))
    log.info("跳过：未发布 %d 个 / 无 interview 块 %d 个",
             result.skipped_unpublished, result.skipped_no_interview)

    if result.issues:
        log.warning("待修 %d 个（已跳过，未上站）：", len(result.issues))
        for issue in result.issues:
            log.warning("  · %s —— %s", issue.path, issue.reason)
    else:
        log.info("待修 0 个")

    if result.unsafe:
        log.error("未转义 HTML %d 处（**必须修**，会在浏览器里真实执行/发起请求）：",
                  len(result.unsafe))
        for u in result.unsafe:
            log.error("  · %s", u)
    else:
        log.info("未转义 HTML 0 处")

    log.info("图谱：全库 %d 页", graph.total_pages)
    if graph.broken:
        log.warning("死链 %d 条（指向不存在的页面，点进去是空的）：", len(graph.broken))
        for b in graph.broken:
            log.warning("  · %s", b)
    else:
        log.info("死链 0 条")

    if graph.orphans:
        rate = len(graph.orphans) / graph.total_pages * 100 if graph.total_pages else 0
        log.warning("孤页 %d 个（无任何入链，占 %.1f%%，健康目标 <5%%）：",
                    len(graph.orphans), rate)
        for o in graph.orphans:
            log.warning("  · %s", o)
    else:
        log.info("孤页 0 个")

    if not result.pages:
        log.warning("没有任何页面可上站。请检查 wiki/ 下的页面是否填了 interview 块。")

    log.info("%s", status)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="知识库 → kb.json 构建")
    parser.add_argument("--dry-run", action="store_true", help="只校验与统计，不写文件")
    parser.add_argument("--force", action="store_true", help="内容未变时也强制重写产物")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出处理详情")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    try:
        result = scan_wiki(verbose=args.verbose)
        payload = build_payload(result)
        graph = check_graph()

        status = "dry-run，未写入文件"
        if not args.dry_run:
            if should_skip_write(payload, force=args.force):
                status = "内容未变（%s），跳过写入" % payload["version"]
            else:
                OUTPUT_PATH.write_text(
                    json.dumps(payload, ensure_ascii=False, indent=1),
                    encoding="utf-8",
                )
                status = "已写入：%s" % OUTPUT_PATH

        report(result, graph=graph, status=status)
        log.info("版本：%s", payload["version"])
        return 1 if (graph.broken or result.unsafe) else 0
    except Exception as exc:  # noqa: BLE001
        log.exception("构建失败：%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
