#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_kb.py 的回归测试。

覆盖的四条不变式（都是「漏了也不会报错、只会在线上表现为点进去什么都没有」的那种）：
  1. publish 的「未发布」判定必须 fail-safe —— 写成 `"false"` / `0` 也要挡住；
  2. 代码块 / 行内代码里的 `[[示例]]` 不能被当成双链；正文里的原始 HTML 必须被检出；
  3. 检测到未转义 HTML 时必须**拒绝写入产物**（判定先于写入，不能 fail-open）；
  4. 产物写入幂等 —— 判据是 contentHash，与日期、构建时刻无关。

运行：
    /Users/tigerwen/.workbuddy/binaries/python/envs/default/bin/python -m pytest site/tests -v
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
if str(SITE_DIR) not in sys.path:
    sys.path.insert(0, str(SITE_DIR))

import build_kb  # noqa: E402

#: 临时知识库的落点（仓库内、已 gitignore）
TMP_ROOT = Path(__file__).resolve().parent / ".tmp"


# --------------------------------------------------------------------------- #
# 夹具
# --------------------------------------------------------------------------- #


def _page_md(title: str, cat: str = "theory", kind: str = "knowledge",
             body: str = "正文内容。", publish: str | None = "true",
             with_interview: bool = True) -> str:
    """拼一个最小可用的 wiki 页面。"""
    lines = ["---", f"title: {title}"]
    if publish is not None:
        lines.append(f"publish: {publish}")
    if with_interview:
        lines += ["interview:", f"  cat: {cat}", f"  kind: {kind}", "  level: 高级"]
    lines += ["---", "", f"# {title}", "", body, ""]
    return "\n".join(lines)


@pytest.fixture()
def tmp_kb(monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """在仓库内 .tmp/ 下搭一个临时知识库。

    刻意不用 pytest 的 tmp_path：它的 basetemp 落在系统临时目录，
    在受限环境里创建目录会被沙箱直接拒绝；放在仓库内既可控又便于清理
    （.tmp/ 已在 .gitignore 中）。
    """
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT, ignore_errors=True)
    wiki = TMP_ROOT / "wiki"
    wiki.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(build_kb, "KB_ROOT", TMP_ROOT)
    monkeypatch.setattr(build_kb, "WIKI_DIR", wiki)
    monkeypatch.setattr(build_kb, "OUTPUT_PATH", TMP_ROOT / "kb.json")
    try:
        yield TMP_ROOT
    finally:
        shutil.rmtree(TMP_ROOT, ignore_errors=True)


# --------------------------------------------------------------------------- #
# 1. publish 判定
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("raw", [False, "false", '"false"', "'false'", "no", "off", "0", 0, "", " FALSE "])
def test_unpublished_recognized_regardless_of_literal_style(raw: Any) -> None:
    """字符串 / 数字形态的「假值」也必须被识别为未发布。

    这些写法在 YAML 里不会解析成布尔 False，旧实现用 `is False` 判定会直接放行 ——
    publish 是隐私开关，方向不能反。
    """
    unpublished, _ = build_kb.is_unpublished({"publish": raw})
    assert unpublished is True, f"publish={raw!r} 未被识别为未发布"


@pytest.mark.parametrize("raw", [True, "true", "yes", 1])
def test_published_when_truthy(raw: Any) -> None:
    """`publish: true` 及其常见写法不应被误判为未发布。"""
    unpublished, _ = build_kb.is_unpublished({"publish": raw})
    assert unpublished is False


def test_publish_absent_defaults_to_published() -> None:
    """frontmatter 里没写 publish 时默认发布 —— 与原有语义一致。"""
    assert build_kb.is_unpublished({})[0] is False


@pytest.mark.parametrize("raw", ['"false"', 0])
def test_suspicious_publish_emits_warning(raw: Any) -> None:
    """可疑写法要显式告警，而不是静默按未发布处理。"""
    unpublished, warn = build_kb.is_unpublished({"publish": raw})
    assert unpublished is True
    assert warn and "publish" in warn


def test_quoted_false_page_does_not_reach_site(tmp_kb: Path) -> None:
    """端到端：publish 写成字符串 "false" 的页面不得进入产物。"""
    (tmp_kb / "wiki" / "机密页.md").write_text(
        _page_md("机密页", publish='"false"'), encoding="utf-8")
    (tmp_kb / "wiki" / "公开页.md").write_text(_page_md("公开页"), encoding="utf-8")

    result = build_kb.scan_wiki()
    titles = {p.title for p in result.pages}
    assert titles == {"公开页"}
    assert result.skipped_unpublished == 1


# --------------------------------------------------------------------------- #
# 2. 双链 / 代码 / 原始 HTML
# --------------------------------------------------------------------------- #


def test_wikilink_in_code_fence_is_left_alone() -> None:
    """代码块里的 `[[示例]]` 是示例写法，不应变成可点链接。"""
    md = "示例：\n\n```python\nx = '[[页面名]]'\n```\n"
    out = build_kb.replace_wikilinks(md)
    assert 'class="wl"' not in out
    assert "[[页面名]]" in out


def test_wikilink_in_inline_code_is_left_alone() -> None:
    out = build_kb.replace_wikilinks("写法是 `[[页面名]]` 这样。")
    assert 'class="wl"' not in out


def test_wikilink_outside_code_becomes_span() -> None:
    out = build_kb.replace_wikilinks("见 [[性能测试基础]] 与 [[其他页|别名]]。")
    assert 'data-page="性能测试基础"' in out
    assert ">别名<" in out


def test_extract_links_ignores_code_samples() -> None:
    md = "真链接 [[真页面]]，代码里 `[[假页面]]`，代码块：\n\n```\n[[也不是]]\n```\n"
    assert build_kb.extract_links(md) == ["真页面"]


def test_raw_html_in_body_is_detected() -> None:
    """正文里塞原始 HTML 必须被检出 —— 否则会在浏览器里真实执行。"""
    leaked = build_kb.unsafe_html_in("<p>看这个</p><script>alert(1)</script>")
    assert "<script" in leaked


def test_clean_rendered_body_has_no_unsafe_tags() -> None:
    html = build_kb.render_body("普通段落，含 `code` 与 [[链接]]。", "标题")
    assert build_kb.unsafe_html_in(html) == []


def test_h1_duplicating_title_is_stripped() -> None:
    """卡片本身已展示标题，正文里重复的一级标题应去掉。"""
    html = build_kb.render_body("# 同一个标题\n\n正文。", "同一个标题")
    assert "<h1" not in html


# --------------------------------------------------------------------------- #
# 3. fail-closed：检测到危险内容必须拒绝落盘
# --------------------------------------------------------------------------- #


def test_build_refuses_to_write_when_unsafe(tmp_kb: Path, caplog: pytest.LogCaptureFixture) -> None:
    """存在未转义 HTML 时，产物必须保持原样不变。

    旧实现是「先写产物、后定退出码」：产物已经更新，检测结果只剩一个退出码，
    等于 fail-open。这里锁住正确的顺序。
    """
    out = tmp_kb / "kb.json"
    out.write_text('{"contentHash":"previous-safe-build"}', encoding="utf-8")

    (tmp_kb / "wiki" / "危险页.md").write_text(
        _page_md("危险页", body="正文 <img src=x onerror=alert(1)> 结束"),
        encoding="utf-8",
    )

    code = build_kb.main([])

    assert code == 1, "检出危险内容时退出码必须非零"
    assert json.loads(out.read_text(encoding="utf-8"))["contentHash"] == "previous-safe-build", \
        "危险内容不得覆盖上一版安全产物"


def test_build_writes_when_clean(tmp_kb: Path) -> None:
    """正常内容应当照常落盘，并带上 contentHash。"""
    (tmp_kb / "wiki" / "正常页.md").write_text(_page_md("正常页"), encoding="utf-8")

    assert build_kb.main([]) == 0
    payload = json.loads((tmp_kb / "kb.json").read_text(encoding="utf-8"))
    assert payload["contentHash"]
    assert [i["title"] for i in payload["data"]["items"]] == ["正常页"]


# --------------------------------------------------------------------------- #
# 4. 幂等与版本
# --------------------------------------------------------------------------- #


def _mk_page(**kw: Any) -> build_kb.KbPage:
    base: dict[str, Any] = dict(
        id="wiki/x", title="X", cat="theory", kind="knowledge", level="高级",
        question="", domain="", updated="2026-09-12", confidence="high",
    )
    base.update(kw)
    return build_kb.KbPage(**base)


def test_content_digest_ignores_build_time() -> None:
    """指纹只取决于内容 —— 不能掺入日期 / 构建时刻，否则每天都会产生伪 diff。"""
    pages = [_mk_page()]
    assert build_kb.content_digest(pages) == build_kb.content_digest([_mk_page()])


def test_content_digest_changes_with_content() -> None:
    assert build_kb.content_digest([_mk_page()]) != build_kb.content_digest([_mk_page(body="改了")])


def test_version_is_date_prefix_plus_digest() -> None:
    """版本号形如 kb-YYYY.MM.DD-<digest>：日期段只供人读，判等一律用 contentHash。"""
    digest = build_kb.content_digest([_mk_page()])
    version = build_kb.compute_version(digest)

    assert version.startswith("kb-")
    assert version.endswith("-" + digest)
    date_part = version[len("kb-"): -len(digest) - 1]
    assert re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", date_part), f"版本号日期段异常：{version}"


def test_should_skip_write_uses_content_hash(tmp_kb: Path) -> None:
    """幂等判据必须是 contentHash —— 不能拿 version（含日期）或文件整体当判据。"""
    payload = {"contentHash": "abc12345", "version": "kb-2026.01.01-abc12345"}
    build_kb.OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    assert build_kb.should_skip_write(payload) is True
    # 换一天：version 变了但内容没变 → 仍应跳过写入
    assert build_kb.should_skip_write(
        {"contentHash": "abc12345", "version": "kb-2030.12.31-abc12345"}) is True
    # 内容真变了 → 必须写
    assert build_kb.should_skip_write(
        {"contentHash": "zzz", "version": "kb-2026.01.01-zzz"}) is False
    assert build_kb.should_skip_write(payload, force=True) is False


def test_missing_content_hash_is_treated_as_changed(tmp_kb: Path) -> None:
    """缺 contentHash 的旧产物视为已变更 —— 写入一次即完成迁移。"""
    build_kb.OUTPUT_PATH.write_text('{"version":"kb-2026.01.01-old"}', encoding="utf-8")
    assert build_kb.should_skip_write({"contentHash": "new"}) is False


# --------------------------------------------------------------------------- #
# 5. 图谱检查
# --------------------------------------------------------------------------- #


def test_link_to_missing_page_is_broken(tmp_kb: Path) -> None:
    (tmp_kb / "wiki" / "A.md").write_text(_page_md("A", body="见 [[不存在的页]]。"), encoding="utf-8")

    graph = build_kb.check_graph()
    assert len(graph.broken) == 1
    assert "不存在的页" in graph.broken[0]


def test_link_to_unpublished_page_is_unreachable_not_broken(tmp_kb: Path) -> None:
    """目标存在但不上站 —— 不能算死链（文件确实在），也不能放过（点进去是空的）。"""
    (tmp_kb / "wiki" / "A.md").write_text(_page_md("A", body="见 [[隐页]]。"), encoding="utf-8")
    (tmp_kb / "wiki" / "隐页.md").write_text(
        _page_md("隐页", with_interview=False), encoding="utf-8")

    graph = build_kb.check_graph()
    assert graph.broken == []
    assert len(graph.unreachable) == 1
    assert "隐页" in graph.unreachable[0]


def test_link_between_unpublished_pages_is_not_reported(tmp_kb: Path) -> None:
    """两个都不上站的页面互相引用不构成线上问题，不应产生噪声。"""
    (tmp_kb / "wiki" / "隐A.md").write_text(
        _page_md("隐A", with_interview=False, body="见 [[隐B]]。"), encoding="utf-8")
    (tmp_kb / "wiki" / "隐B.md").write_text(
        _page_md("隐B", with_interview=False), encoding="utf-8")

    graph = build_kb.check_graph()
    assert graph.unreachable == []


# --------------------------------------------------------------------------- #
# 6. 字段校验与分类映射
# --------------------------------------------------------------------------- #


def test_invalid_cat_is_reported_not_raised(tmp_kb: Path) -> None:
    """cat 非法 → 记入待修清单并跳过，不中断整体构建。"""
    (tmp_kb / "wiki" / "坏页.md").write_text(
        _page_md("坏页", cat="not-a-real-cat"), encoding="utf-8")
    (tmp_kb / "wiki" / "好页.md").write_text(_page_md("好页"), encoding="utf-8")

    result = build_kb.scan_wiki()
    assert [p.title for p in result.pages] == ["好页"]
    assert len(result.issues) == 1
    assert "not-a-real-cat" in result.issues[0].reason


def test_repo_cat_mapping_chain_is_consistent() -> None:
    """真实仓库上，分类的四道映射必须首尾贯通（构建脚本 ↔ KB_CAT_MAP ↔ CAT_DICT ↔ CSS）。"""
    problems = build_kb.check_cat_mirror()
    assert problems == [], "分类映射链存在断点：\n" + "\n".join(problems)


def test_check_graph_on_real_repo_finds_no_broken_links() -> None:
    """真实仓库不得存在死链 —— 死链会让构建返回非零退出码。"""
    graph = build_kb.check_graph()
    assert graph.broken == [], "真实仓库存在死链：\n" + "\n".join(graph.broken)
