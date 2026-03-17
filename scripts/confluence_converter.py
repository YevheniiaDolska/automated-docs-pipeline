#!/usr/bin/env python3
"""Convert Confluence storage/content HTML to Markdown."""

from __future__ import annotations

import html
import re


class ConfluenceToMarkdownConverter:
    """Lightweight converter tuned for docs migration workflows."""

    def convert(self, content: str) -> str:
        if not content:
            return ""

        text = html.unescape(content)
        text = self._convert_code_macros(text)
        text = self._convert_admonition_macros(text)
        text = self._convert_headings(text)
        text = self._convert_tables(text)
        text = self._convert_lists(text)
        text = self._convert_links(text)
        text = self._convert_images(text)
        text = self._convert_inline_formatting(text)
        text = self._convert_block_elements(text)
        text = self._strip_remaining_tags(text)
        text = self._normalize_whitespace(text)
        return text.strip()

    def _convert_code_macros(self, text: str) -> str:
        pattern = re.compile(
            r'<ac:structured-macro[^>]*ac:name="code"[^>]*>(.*?)</ac:structured-macro>',
            re.DOTALL | re.IGNORECASE,
        )

        def repl(match: re.Match[str]) -> str:
            block = match.group(1)
            lang_match = re.search(r"ac:name=\"language\"[^>]*>([^<]+)<", block, re.IGNORECASE)
            language = (lang_match.group(1).strip() if lang_match else "").lower()
            code_match = re.search(
                r"<ac:plain-text-body><!\[CDATA\[(.*?)\]\]></ac:plain-text-body>",
                block,
                re.DOTALL | re.IGNORECASE,
            )
            code = code_match.group(1).strip() if code_match else self._strip_remaining_tags(block).strip()
            return f"\n```{language}\n{code}\n```\n"

        return pattern.sub(repl, text)

    def _convert_admonition_macros(self, text: str) -> str:
        macro_to_kind = {
            "info": "info",
            "warning": "warning",
            "note": "note",
            "tip": "tip",
        }

        for macro, kind in macro_to_kind.items():
            pattern = re.compile(
                rf'<ac:structured-macro[^>]*ac:name="{macro}"[^>]*>(.*?)</ac:structured-macro>',
                re.DOTALL | re.IGNORECASE,
            )

            def repl(match: re.Match[str], kind_value: str = kind, macro_name: str = macro) -> str:
                body = self._extract_macro_body(match.group(1)).strip()
                title = macro_name.capitalize()
                indented = "\n".join(f"    {line}" if line else "" for line in body.splitlines())
                return f"\n!!! {kind_value} \"{title}\"\n{indented}\n"

            text = pattern.sub(repl, text)

        text = re.sub(
            r'<ac:structured-macro[^>]*ac:name="toc"[^>]*/?>.*?</ac:structured-macro>',
            "",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        return text

    def _extract_macro_body(self, macro_content: str) -> str:
        rich = re.search(r"<ac:rich-text-body>(.*?)</ac:rich-text-body>", macro_content, re.DOTALL | re.IGNORECASE)
        if rich:
            return self._strip_remaining_tags(rich.group(1))
        plain = re.search(r"<ac:plain-text-body><!\[CDATA\[(.*?)\]\]></ac:plain-text-body>", macro_content, re.DOTALL | re.IGNORECASE)
        if plain:
            return plain.group(1)
        return self._strip_remaining_tags(macro_content)

    def _convert_headings(self, text: str) -> str:
        for level in range(6, 0, -1):
            text = re.sub(
                rf"<h{level}[^>]*>(.*?)</h{level}>",
                lambda m, l=level: f"\n{'#' * l} {self._strip_remaining_tags(m.group(1)).strip()}\n",
                text,
                flags=re.DOTALL | re.IGNORECASE,
            )
        return text

    def _convert_tables(self, text: str) -> str:
        table_pattern = re.compile(r"<table[^>]*>(.*?)</table>", re.DOTALL | re.IGNORECASE)

        def table_repl(match: re.Match[str]) -> str:
            table = match.group(1)
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.DOTALL | re.IGNORECASE)
            parsed_rows: list[list[str]] = []
            for row in rows:
                cells = re.findall(r"<(?:th|td)[^>]*>(.*?)</(?:th|td)>", row, re.DOTALL | re.IGNORECASE)
                values = [self._strip_remaining_tags(cell).strip() for cell in cells]
                if values:
                    parsed_rows.append(values)
            if not parsed_rows:
                return ""

            header = parsed_rows[0]
            lines = [f"| {' | '.join(header)} |", f"| {' | '.join(['---'] * len(header))} |"]
            for row in parsed_rows[1:]:
                if len(row) < len(header):
                    row = row + [""] * (len(header) - len(row))
                lines.append(f"| {' | '.join(row[:len(header)])} |")
            return "\n" + "\n".join(lines) + "\n"

        return table_pattern.sub(table_repl, text)

    def _convert_lists(self, text: str) -> str:
        text = re.sub(r"<li[^>]*>(.*?)</li>", lambda m: f"\n- {self._strip_remaining_tags(m.group(1)).strip()}", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"</?(?:ul|ol)[^>]*>", "", text, flags=re.IGNORECASE)
        return text

    def _convert_links(self, text: str) -> str:
        text = re.sub(
            r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            lambda m: f"[{self._strip_remaining_tags(m.group(2)).strip()}]({m.group(1).strip()})",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        text = re.sub(
            r'<ac:link>\s*<ri:page[^>]*ri:content-title="([^"]+)"[^>]*/>\s*</ac:link>',
            lambda m: f"[{m.group(1)}](./{self._slugify(m.group(1))}.md)",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        return text

    def _convert_images(self, text: str) -> str:
        text = re.sub(
            r'<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"[^>]*/?>',
            lambda m: f"![{m.group(2)}]({m.group(1)})",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r'<ac:image>\s*<ri:attachment[^>]*ri:filename="([^"]+)"[^>]*/>\s*</ac:image>',
            lambda m: f"![](/attachments/{m.group(1)})",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        return text

    def _convert_inline_formatting(self, text: str) -> str:
        text = re.sub(r"<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>", r"**\1**", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<(?:em|i)[^>]*>(.*?)</(?:em|i)>", r"*\1*", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<code[^>]*>(.*?)</code>", lambda m: f"`{self._strip_remaining_tags(m.group(1)).strip()}`", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<(?:del|s)[^>]*>(.*?)</(?:del|s)>", r"~~\1~~", text, flags=re.DOTALL | re.IGNORECASE)
        return text

    def _convert_block_elements(self, text: str) -> str:
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<p[^>]*>(.*?)</p>", lambda m: f"\n{self._strip_remaining_tags(m.group(1)).strip()}\n", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<pre[^>]*>(.*?)</pre>", lambda m: f"\n```\n{self._strip_remaining_tags(m.group(1)).strip()}\n```\n", text, flags=re.DOTALL | re.IGNORECASE)
        return text

    def _strip_remaining_tags(self, text: str) -> str:
        text = re.sub(r"<[^>]+>", "", text)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        text = text.replace("\r\n", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        return text.strip()

    def _slugify(self, title: str) -> str:
        slug = title.lower().strip()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"\s+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug[:120].strip("-") or "page"
