#!/usr/bin/env python3
"""Check local HTML, resources and links without network or browser execution."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


class Document(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.references: list[tuple[str, bool]] = []
        self.anchors: list[str] = []
        self.title_parts: list[str] = []
        self.viewport = False
        self._title = False
        self._style = False
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get('id'):
            key = values['id']
            if key in self.ids:
                self.duplicate_ids.add(key)
            self.ids.add(key)
        if tag == 'title':
            self._title = True
        if tag == 'style':
            self._style = True
        if tag == 'meta' and values.get('name', '').lower() == 'viewport':
            self.viewport = 'width=device-width' in values.get('content', '').replace(' ', '')
        if tag == 'a' and values.get('href'):
            self.anchors.append(values['href'])
        for attribute in ('href', 'src', 'poster', 'data'):
            value = values.get(attribute)
            if not value:
                continue
            resource = attribute == 'src' or attribute == 'poster' or (attribute == 'data' and tag == 'object')
            if tag == 'link':
                resource = bool(set(values.get('rel', '').lower().split()) & {'stylesheet', 'icon', 'preload', 'modulepreload'})
            if tag in {'a', 'link', 'use', 'image'} or resource:
                self.references.append((value, resource or tag == 'image'))
        # A self-contained page cannot rely on srcset. Do not guess its full grammar.
        if values.get('srcset'):
            self.references.append(('srcset:' + values['srcset'], True))

    def handle_endtag(self, tag):
        if tag == 'title':
            self._title = False
        if tag == 'style':
            self._style = False

    def handle_data(self, data):
        if self._title:
            self.title_parts.append(data)
        if self._style:
            for match in re.finditer(r'url\(\s*[\'"]?([^\'"\s)]+)', data, re.I):
                self.references.append((match.group(1), True))
            for match in re.finditer(r'@import\s+[\'"]([^\'"]+)', data, re.I):
                self.references.append((match.group(1), True))


class HtmlChecker:
    def __init__(self, root: Path, base_path: str = "/", single_file: bool = False):
        self.root = root.resolve()
        self.base_path = base_path
        self.single_file = single_file
        self.documents: dict[Path, Document] = {}

    def within_root(self, target: Path) -> Path:
        resolved = target.resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError('链接或目录超出站点根目录')
        return resolved

    def page_file(self, route: str) -> Path:
        if '\\' in route or '%' in route or urlsplit(route).scheme or route.startswith('/'):
            raise ValueError('页面路径必须是不含百分号转义的站内相对目录或 HTML 文件')
        if urlsplit(route).query or urlsplit(route).fragment or '..' in Path(route).parts:
            raise ValueError('页面路径不可含查询参数、锚点或上级目录')
        target = self.within_root(self.root / route)
        if target.is_dir():
            target = self.within_root(target / 'index.html')
        if target.suffix.lower() != '.html' or not target.is_file():
            raise ValueError('页面目录中缺少 index.html，或指定的 HTML 文件不存在')
        return target

    def document(self, path: Path) -> Document:
        if path not in self.documents:
            self.documents[path] = Document(path.read_text(encoding='utf-8'))
        return self.documents[path]

    def local_reference(self, page: Path, ref: str) -> tuple[Path | None, str]:
        parsed = urlsplit(ref)
        scheme = parsed.scheme.lower()
        if scheme in {'http', 'https', 'mailto', 'tel', 'data', 'blob'} or parsed.netloc:
            return None, ''
        if scheme:
            raise ValueError('不支持的本地链接协议：' + scheme)
        value = unquote(parsed.path)
        if '\\' in value:
            raise ValueError('本地链接含反斜杠，无法可靠映射到站点 URL')
        if value.startswith('/'):
            if not value.startswith(self.base_path):
                raise ValueError('根路径链接可能跳过项目基路径；使用相对链接或传入正确的 --base-path')
            target = self.root / value[len(self.base_path):]
        else:
            target = page.parent / value if value else page
        target = self.within_root(target)
        if target.is_dir():
            target = self.within_root(target / 'index.html')
        return target, unquote(parsed.fragment)

    def check(self, page: Path) -> list[str]:
        issues = []
        text = page.read_text(encoding='utf-8')
        doc = self.document(page)
        if not ''.join(doc.title_parts).strip():
            issues.append('缺少非空 title')
        if not doc.viewport:
            issues.append('缺少 width=device-width 的 viewport')
        if doc.duplicate_ids:
            issues.append('重复 ID：' + ', '.join(sorted(doc.duplicate_ids)))
        if re.search(r'__(?:MARKET_DATA|PAGE_STYLES|PAGE_SCRIPT)__', text):
            issues.append('存在尚未替换的构建占位符')
        seen = set()
        for ref, resource in doc.references:
            if (ref, resource) in seen:
                continue
            seen.add((ref, resource))
            if ref.startswith('srcset:'):
                if self.single_file:
                    issues.append('单文件模式下请将 srcset 资源内嵌或移除该模式后人工核对')
                continue
            parsed = urlsplit(ref)
            if parsed.scheme.lower() == 'file':
                issues.append('页面引用本机 file: 路径')
                continue
            if resource and self.single_file and parsed.scheme not in {'data', 'blob'} and not ref.startswith('#'):
                issues.append('单文件模式仍引用运行资源：' + ref)
            try:
                target, fragment = self.local_reference(page, ref)
                if target is None:
                    continue
                if not target.is_file():
                    issues.append('本地链接或资源不存在：' + ref)
                elif fragment and target.suffix.lower() == '.html' and fragment not in self.document(target).ids:
                    issues.append('HTML 锚点不存在：' + ref)
            except (ValueError, UnicodeError, OSError) as exc:
                issues.append(f'无法验证链接 {ref!r}：{exc}')
        return issues

    def homepage_has(self, page: Path) -> bool:
        home = self.page_file('.')
        if page == home:
            return True
        for ref in self.document(home).anchors:
            try:
                target, _ = self.local_reference(home, ref)
                if target == page:
                    return True
            except (ValueError, OSError):
                continue
        return False

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--page', action='append', help='Relative HTML path or directory; repeatable')
    parser.add_argument('--base-path', default='/', help='Expected URL path prefix; no network request')
    parser.add_argument('--require-single-file', action='store_true')
    parser.add_argument('--require-homepage-link', action='store_true')
    parser.add_argument('--output', type=Path, help='Optional JSON record outside the output directory')
    args = parser.parse_args(argv)
    if not args.root.is_dir():
        parser.error('--root must be an existing directory')
    base = urlsplit(args.base_path)
    if (not args.base_path.startswith('/') or args.base_path.startswith('//')
            or not args.base_path.endswith('/') or base.scheme or base.netloc
            or base.query or base.fragment or '%' in args.base_path
            or '..' in Path(args.base_path).parts or "\\" in args.base_path):
        parser.error('--base-path must be an absolute URL path ending in /')
    if args.output and args.output.resolve().is_relative_to(args.root.resolve()):
        parser.error('--output must be outside --root')
    checker = HtmlChecker(args.root, args.base_path, args.require_single_file)
    result = {'checked_at': datetime.now(timezone.utc).isoformat(),
              'root': str(checker.root), 'base_path': args.base_path, 'pages': [], 'ok': True}
    for route in dict.fromkeys(args.page or ['.']):
        record = {'route': route, 'issues': []}
        try:
            page = checker.page_file(route)
            content = page.read_bytes()
            record.update(file=page.relative_to(checker.root).as_posix(), bytes=len(content),
                          sha256=hashlib.sha256(content).hexdigest(), issues=checker.check(page))
            if args.require_homepage_link and not checker.homepage_has(page):
                record['issues'].append('根导航首页尚未收录这个页面')
        except (ValueError, UnicodeError, OSError) as exc:
            record['issues'].append(str(exc))
        record['ok'] = not record['issues']
        result['ok'] = result['ok'] and record['ok']
        result['pages'].append(record)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding='utf-8')
    sys.stdout.write(encoded)
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
