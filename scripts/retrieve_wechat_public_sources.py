#!/usr/bin/env python3
"""Safely retrieve public WeChat album indexes and article bodies.

The workbook is a source index, not an instruction file. This tool only uses
public URLs, keeps a resumable audit trail, and stops on verification pages.
It never sends cookies, pass tickets, login headers or client-only tokens.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

from openpyxl import load_workbook
from html.parser import HTMLParser


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = Path(r"C:\Users\xiajt\Downloads\(公众号数据)表格视图.xlsx")
DEFAULT_OUTPUT = ROOT / "references/knowledge-modules/distilled/retrieval"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8", "Referer": "https://mp.weixin.qq.com/"}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_url(url: str) -> str:
    url = html.unescape(url or "").replace("http://", "https://", 1)
    return url[:-3] if url.endswith("#rd") else url


def request_text(url: str, *, json_accept: bool = False, timeout: int = 30) -> tuple[str, str, int]:
    headers = dict(HEADERS)
    if json_accept:
        headers.update({"Accept": "application/json,text/plain,*/*", "X-Requested-With": "XMLHttpRequest"})
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace"), response.geturl(), response.status


def verification_page(final_url: str, text: str) -> bool:
    haystack = f"{final_url} {text[:30000]}".lower()
    return any(marker in haystack for marker in ("wappoc_appmsgcaptcha", "环境异常", "captcha", "频繁访问", "请完成验证"))


def article_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    return clean(html.unescape(re.sub(r"<[^>]+>", " ", match.group(1)))) if match else ""


class ContentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if self.depth == 0 and attrs_map.get("id") == "js_content":
            self.depth = 1
            return
        if self.depth:
            self.depth += 1
            if tag in {"script", "style"}:
                self.skip += 1

    def handle_endtag(self, tag: str) -> None:
        if not self.depth:
            return
        if tag in {"script", "style"} and self.skip:
            self.skip -= 1
        self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.depth and not self.skip:
            value = clean(data)
            if value:
                self.parts.append(value)


def extract_article_body(text: str) -> str:
    parser = ContentParser()
    parser.feed(text)
    return " ".join(parser.parts)


def parse_album_items(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for block in re.findall(r"<li[^>]*class=[\"'][^\"']*js_album_item[^\"']*[\"'][^>]*>", text, re.I):
        attrs = dict(re.findall(r"([\w-]+)=[\"']([^\"']*)[\"']", block))
        url = normalize_url(attrs.get("data-link", ""))
        if url:
            items.append({"msgid": attrs.get("data-msgid", ""), "itemidx": attrs.get("data-itemidx", ""), "url": url, "title": html.unescape(attrs.get("data-title", ""))})
    return items


def parse_album_json(text: str) -> tuple[list[dict[str, str]], bool]:
    payload = json.loads(text)
    response = payload.get("getalbum_resp", {})
    items = []
    for item in response.get("article_list", []) or []:
        if not isinstance(item, dict):
            continue
        items.append({"msgid": str(item.get("msgid", "")), "itemidx": str(item.get("itemidx", "")), "url": normalize_url(item.get("url", "")), "title": clean(item.get("title", ""))})
    return [item for item in items if item["url"]], int(response.get("continue_flag", 0)) == 1


def album_identity(url: str) -> tuple[str, str]:
    query = parse_qs(urlparse(url).query)
    return query.get("__biz", [""])[0], query.get("album_id", [""])[0]


def load_workbook_sources(path: Path) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
    ws = load_workbook(path, read_only=True, data_only=True).active
    headers = [clean(v) for v in next(ws.iter_rows(values_only=True))]
    index = {name: i for i, name in enumerate(headers)}
    rows: list[dict[str, Any]] = []
    albums: dict[str, list[int]] = defaultdict(list)
    for row_no, values in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        body = clean(values[index.get("正文", -1)]) if index.get("正文") is not None else ""
        if body:
            continue
        url = normalize_url(clean(values[index.get("链接", -1)])) if index.get("链接") is not None else ""
        row = {"row": row_no, "title": clean(values[index.get("标题", -1)]), "url": url, "account": clean(values[index.get("公众号名", -1)]), "published_at": clean(values[index.get("发布日期", -1)]), "link_kind": "album" if "appmsgalbum" in url else "direct" if "/s/" in url else "other"}
        rows.append(row)
        if row["link_kind"] == "album":
            albums[url].append(row_no)
    return rows, albums


def read_done(path: Path, key: str) -> set[str]:
    if not path.exists():
        return set()
    done: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                value = json.loads(line).get(key)
                if value:
                    done.add(str(value))
            except json.JSONDecodeError:
                continue
    return done


def title_key(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").replace("\u200b", "").replace("_x0008_", ""))


def album_article_rows(path: Path, source_rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Read already fetched album pages and create a deduplicated article queue."""
    queue: dict[str, dict[str, Any]] = {}
    targets: dict[str, set[str]] = defaultdict(set)
    target_meta: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in source_rows:
        if row.get("link_kind") == "album":
            key = title_key(row.get("title", ""))
            targets[row["url"]].add(key)
            target_meta[(row["url"], key)].append(int(row["row"]))
    matched: dict[str, set[str]] = defaultdict(set)
    unmatched: list[dict[str, Any]] = []
    if not path.exists():
        return queue, unmatched
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            album = json.loads(line)
        except json.JSONDecodeError:
            continue
        for item in album.get("items", []) or []:
            url = normalize_url(str(item.get("url", "")))
            if not url:
                continue
            target_titles = targets.get(album.get("album_url", ""), set())
            item_title_key = title_key(item.get("title", ""))
            if target_titles and item_title_key not in target_titles:
                continue
            matched[album.get("album_url", "")].add(item_title_key)
            queue.setdefault(url, {
                "row": None,
                "source_rows": album.get("source_rows", []),
                "title": clean(item.get("title", "")),
                "url": url,
                "account": "",
                "published_at": "",
                "link_kind": "album_discovered",
                "album_id": album.get("album_id", ""),
            })
    for album_url, title_keys in targets.items():
        for key in sorted(title_keys - matched.get(album_url, set())):
            unmatched.append({"album_url": album_url, "title_key": key, "source_rows": target_meta.get((album_url, key), [])})
    return queue, unmatched


def append_jsonl(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    handle.flush()


def fetch_album(url: str, source_rows: list[int], delay: float, max_pages: int = 100) -> dict[str, Any]:
    biz, album_id = album_identity(url)
    result: dict[str, Any] = {"album_url": url, "biz": biz, "album_id": album_id, "source_rows": source_rows, "items": [], "status": "ok", "pages": 0}
    if not biz or not album_id:
        result["status"] = "invalid_album_url"
        return result
    try:
        page_url = f"https://mp.weixin.qq.com/mp/appmsgalbum?{urlencode({'__biz': biz, 'action': 'getalbum', 'album_id': album_id})}"
        text, final_url, status = request_text(page_url)
        result.update({"http_status": status, "final_url": final_url})
        if verification_page(final_url, text):
            result["status"] = "verification_required"
            return result
        initial = parse_album_items(text)
        result["items"].extend(initial)
        result["pages"] = 1
        cursor = initial[-1] if initial else None
        continue_flag = bool(cursor) and "continue_flag" in text
        for _ in range(max_pages - 1):
            if not cursor or not continue_flag:
                break
            time.sleep(delay)
            query = {"__biz": biz, "action": "getalbum", "album_id": album_id, "count": "10", "begin_msgid": cursor["msgid"], "begin_itemidx": cursor["itemidx"], "f": "json"}
            api_url = "https://mp.weixin.qq.com/mp/appmsgalbum?" + urlencode(query)
            api_text, api_final, api_status = request_text(api_url, json_accept=True)
            if verification_page(api_final, api_text):
                result["status"] = "verification_required"
                break
            page, continue_flag = parse_album_json(api_text)
            if not page:
                break
            result["items"].extend(page)
            result["pages"] += 1
            cursor = page[-1]
        unique: dict[str, dict[str, str]] = {}
        for item in result["items"]:
            unique.setdefault(item["url"], item)
        result["items"] = list(unique.values())
        result["item_count"] = len(result["items"])
        return result
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        result["status"] = "error"
        result["error"] = str(exc)
        return result


def fetch_article(row: dict[str, Any], delay: float) -> dict[str, Any]:
    result = {**row, "status": "unknown", "body": ""}
    try:
        text, final_url, status = request_text(row["url"])
        result.update({"http_status": status, "final_url": final_url, "html_bytes": len(text)})
        if verification_page(final_url, text):
            result["status"] = "verification_required"
            return result
        body = extract_article_body(text)
        result["title_from_page"] = article_title(text)
        result["body"] = body
        result["status"] = "retrieved" if body else "no_js_content"
        return result
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        result["status"] = "error"
        result["error"] = str(exc)
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--mode", choices=("albums", "articles", "all"), default="albums")
    parser.add_argument("--max-albums", type=int, default=0, help="0 means all unique album URLs")
    parser.add_argument("--max-articles", type=int, default=0, help="0 means all direct workbook URLs")
    parser.add_argument("--delay", type=float, default=0.6)
    parser.add_argument("--workers", type=int, default=1, help="article fetch workers; keep low to reduce public endpoint load")
    args = parser.parse_args()
    rows, albums = load_workbook_sources(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "empty-source-index.json").write_text(json.dumps({"source_sha256": __import__("hashlib").sha256(args.input.read_bytes()).hexdigest(), "rows": rows, "unique_albums": len(albums), "unique_direct_articles": len({row['url'] for row in rows if row['link_kind'] == 'direct'})}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    album_path = args.output_dir / "album-pages.jsonl"
    article_path = args.output_dir / "article-bodies.jsonl"
    done_albums = read_done(album_path, "album_url")
    done_articles = read_done(article_path, "url")
    album_items: list[dict[str, Any]] = []
    if args.mode in {"albums", "all"}:
        album_urls = [url for url in albums if url not in done_albums]
        if args.max_albums:
            album_urls = album_urls[: args.max_albums]
        with album_path.open("a", encoding="utf-8") as handle:
            for position, url in enumerate(album_urls, start=1):
                result = fetch_album(url, albums[url], args.delay)
                append_jsonl(handle, result)
                album_items.extend(result.get("items", []))
                print(json.dumps({"kind": "album", "position": position, "total": len(album_urls), "album_id": result.get("album_id"), "status": result.get("status"), "items": result.get("item_count", 0)}, ensure_ascii=False))
    if args.mode in {"articles", "all"}:
        direct_rows: dict[str, dict[str, Any]] = {}
        for row in rows:
            if row["link_kind"] == "direct":
                direct_rows.setdefault(row["url"], row)
        discovered, unmatched = album_article_rows(album_path, rows)
        (args.output_dir / "album-unmatched-source-titles.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in unmatched) + ("\n" if unmatched else ""), encoding="utf-8")
        for url, row in discovered.items():
            direct_rows.setdefault(url, row)
        article_urls = [url for url in direct_rows if url not in done_articles]
        if args.max_articles:
            article_urls = article_urls[: args.max_articles]
        def fetch_with_delay(url: str) -> dict[str, Any]:
            time.sleep(args.delay)
            return fetch_article(direct_rows[url], args.delay)

        with article_path.open("a", encoding="utf-8") as handle:
            if args.workers <= 1:
                results = ((url, fetch_with_delay(url)) for url in article_urls)
                for position, (url, result) in enumerate(results, start=1):
                    append_jsonl(handle, result)
                    print(json.dumps({"kind": "article", "position": position, "total": len(article_urls), "url": url, "status": result.get("status"), "body_chars": len(result.get("body", ""))}, ensure_ascii=False))
            else:
                with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as executor:
                    futures = {executor.submit(fetch_with_delay, url): url for url in article_urls}
                    for position, future in enumerate(as_completed(futures), start=1):
                        url = futures[future]
                        result = future.result()
                        append_jsonl(handle, result)
                        print(json.dumps({"kind": "article", "position": position, "total": len(article_urls), "url": url, "status": result.get("status"), "body_chars": len(result.get("body", ""))}, ensure_ascii=False))
    summary = {"source_rows": len(rows), "unique_album_urls": len(albums), "unique_direct_urls": len({row['url'] for row in rows if row['link_kind'] == 'direct'}), "mode": args.mode, "album_results_existing": len(read_done(album_path, "album_url")), "article_results_existing": len(read_done(article_path, "url")), "public_access_policy": "stop on verification_required; no cookies, pass tickets or login credentials"}
    (args.output_dir / "batch-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
