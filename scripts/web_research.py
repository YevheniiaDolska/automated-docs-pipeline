#!/usr/bin/env python3
"""Research a company on the open web for documentation-needs planning.

Queries a search API (Tavily, Brave, or SerpAPI) about the company and its
products, optionally crawls the company domain for existing documentation
signals, and writes a distilled ``company_research.json``. This feeds the
company-template planner so the LLM plans docs against the real product surface,
not just an offline profile.

Web access is external, so the run is gated by the LLM egress policy.

Usage:
    python3 scripts/web_research.py --company "ACME Inc" --domain acme.com \
        --output reports/acme/company_research.json --external-llm-approve-for-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.llm_egress import ensure_external_allowed, load_policy

# Search providers, mirroring the LLM provider registry. Each normalizes to a
# list of {title, url, snippet}.
_SEARCH_PROVIDERS: dict[str, dict[str, str]] = {
    "tavily": {"url": "https://api.tavily.com/search", "style": "tavily", "api_key_env": "TAVILY_API_KEY"},
    "brave": {"url": "https://api.search.brave.com/res/v1/web/search", "style": "brave", "api_key_env": "BRAVE_API_KEY"},
    "serpapi": {"url": "https://serpapi.com/search", "style": "serpapi", "api_key_env": "SERPAPI_API_KEY"},
}


def dotenv_value(key: str, path: str = ".env") -> str:
    """Read one KEY=value from a .env file (repo root). Empty if absent."""
    p = Path(path)
    if not p.exists():
        return ""
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and line.split("=", 1)[0].strip() == key:
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def env_with_dotenv(env_file: str = ".env") -> dict[str, str]:
    """os.environ merged with search-provider keys from .env (environ wins)."""
    import os

    merged = dict(os.environ)
    for cfg in _SEARCH_PROVIDERS.values():
        key = cfg["api_key_env"]
        if not merged.get(key, "").strip():
            value = dotenv_value(key, env_file)
            if value:
                merged[key] = value
    return merged


def resolve_search_provider(name: str, env: dict[str, str]) -> dict[str, str] | None:
    """Resolve a provider by name, or auto-pick the first with a key in env."""
    name = str(name or "auto").strip().lower()
    if name != "auto":
        cfg = _SEARCH_PROVIDERS.get(name)
        if cfg:
            out = dict(cfg)
            out["name"] = name
            return out
        return None
    for key, cfg in _SEARCH_PROVIDERS.items():
        if env.get(cfg["api_key_env"], "").strip():
            out = dict(cfg)
            out["name"] = key
            return out
    return None


def _http_json(req: Request, timeout: int) -> dict[str, Any]:
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    data = json.loads(raw or "{}")
    return data if isinstance(data, dict) else {}


def search(provider: dict[str, str], api_key: str, query: str, max_results: int, timeout: int) -> list[dict[str, str]]:
    """Run one search and normalize results to {title, url, snippet}."""
    style = provider["style"]
    if style == "tavily":
        body = json.dumps({"api_key": api_key, "query": query, "max_results": max_results}).encode("utf-8")
        req = Request(provider["url"], data=body, headers={"Content-Type": "application/json"}, method="POST")
        data = _http_json(req, timeout)
        return [
            {"title": str(r.get("title", "")), "url": str(r.get("url", "")), "snippet": str(r.get("content", ""))}
            for r in data.get("results", []) if isinstance(r, dict)
        ][:max_results]
    if style == "brave":
        url = provider["url"] + "?" + urlencode({"q": query, "count": max_results})
        req = Request(url, headers={"X-Subscription-Token": api_key, "Accept": "application/json"}, method="GET")
        data = _http_json(req, timeout)
        results = data.get("web", {}).get("results", []) if isinstance(data.get("web"), dict) else []
        return [
            {"title": str(r.get("title", "")), "url": str(r.get("url", "")), "snippet": str(r.get("description", ""))}
            for r in results if isinstance(r, dict)
        ][:max_results]
    if style == "serpapi":
        url = provider["url"] + "?" + urlencode({"engine": "google", "q": query, "api_key": api_key, "num": max_results})
        req = Request(url, method="GET")
        data = _http_json(req, timeout)
        return [
            {"title": str(r.get("title", "")), "url": str(r.get("link", "")), "snippet": str(r.get("snippet", ""))}
            for r in data.get("organic_results", []) if isinstance(r, dict)
        ][:max_results]
    return []


_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_DESC_RE = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', re.IGNORECASE | re.DOTALL)


def crawl_page(url: str, timeout: int) -> dict[str, str] | None:
    """Fetch one page and extract title + meta description (best effort)."""
    try:
        req = Request(url, headers={"User-Agent": "veriops-research/1.0"}, method="GET")
        with urlopen(req, timeout=timeout) as resp:
            html = resp.read(200_000).decode("utf-8", errors="ignore")
    except (URLError, HTTPError, ValueError, OSError):
        return None
    title = _TITLE_RE.search(html)
    desc = _DESC_RE.search(html)
    return {
        "url": url,
        "title": re.sub(r"\s+", " ", title.group(1)).strip() if title else "",
        "description": re.sub(r"\s+", " ", desc.group(1)).strip() if desc else "",
    }


def build_queries(company: str) -> list[str]:
    company = company.strip()
    return [
        f"{company} products",
        f"{company} API documentation",
        f"{company} SDK developer docs",
        f"{company} pricing plans",
        f"{company} developer platform overview",
    ]


def _domain_urls(domain: str) -> list[str]:
    domain = domain.strip().rstrip("/")
    if not domain:
        return []
    if not domain.startswith("http"):
        base = f"https://{domain}"
    else:
        base = domain
    return [base, f"{base}/docs", f"{base}/developers", f"{base}/api"]


def research_company(
    *,
    company: str,
    domain: str,
    provider: dict[str, str] | None,
    api_key: str,
    max_results: int,
    timeout: int,
    do_crawl: bool,
) -> dict[str, Any]:
    """Aggregate search + crawl signals into a research payload."""
    queries = build_queries(company)
    sources: list[dict[str, str]] = []
    seen: set[str] = set()
    search_errors: list[str] = []
    if provider and api_key:
        for query in queries:
            try:
                for hit in search(provider, api_key, query, max_results, timeout):
                    url = hit.get("url", "")
                    if url and url not in seen:
                        seen.add(url)
                        hit["query"] = query
                        sources.append(hit)
            except (URLError, HTTPError, ValueError, OSError, json.JSONDecodeError) as exc:
                search_errors.append(f"{query}: {exc}")

    domain_pages: list[dict[str, str]] = []
    if do_crawl:
        for url in _domain_urls(domain):
            page = crawl_page(url, timeout)
            if page and (page["title"] or page["description"]):
                domain_pages.append(page)

    return {
        "company": company,
        "domain": domain,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "search_provider": provider["name"] if provider else None,
        "queries": queries,
        "sources": sources,
        "domain_pages": domain_pages,
        "search_errors": search_errors,
        "coverage": {
            "source_count": len(sources),
            "domain_page_count": len(domain_pages),
            "web_search_used": bool(provider and api_key),
        },
    }


def main() -> int:
    import os

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--company", required=True, help="Company name to research")
    parser.add_argument("--domain", default="", help="Company primary domain (for crawl)")
    parser.add_argument("--provider", default="auto", help="Search provider: auto|tavily|brave|serpapi")
    parser.add_argument("--api-key-env", default="", help="Env var for the search key (default: provider default)")
    parser.add_argument("--env-file", default=".env", help="Path to .env with the search key")
    parser.add_argument("--max-results", type=int, default=5, help="Results per query")
    parser.add_argument("--timeout", type=int, default=20, help="Per-request timeout (seconds)")
    parser.add_argument("--no-crawl", action="store_true", help="Skip crawling the company domain")
    parser.add_argument("--output", default="reports/company_research.json", help="Output JSON path")
    parser.add_argument("--runtime-config", default="docsops/config/client_runtime.yml", help="Egress policy config")
    parser.add_argument("--reports-dir", default="reports", help="Reports dir for the egress log")
    parser.add_argument("--external-approve-once", action="store_true", help="Approve one external step")
    parser.add_argument("--external-approve-for-run", action="store_true", help="Approve external use for this run")
    parser.add_argument("--interactive", action="store_true", help="Allow interactive approval prompt")
    args = parser.parse_args()

    env = env_with_dotenv(args.env_file)
    provider = resolve_search_provider(args.provider, env)
    api_key = ""
    if provider:
        api_key_env = args.api_key_env.strip() or provider["api_key_env"]
        api_key = env.get(api_key_env, "").strip()
        if not api_key:
            api_key = dotenv_value(api_key_env, args.env_file)

    # Any web access (search or crawl) is external; gate it.
    policy = load_policy(Path(args.runtime_config))
    approved = ensure_external_allowed(
        policy=policy,
        step="company_web_research",
        reports_dir=Path(args.reports_dir),
        approve_once=bool(args.external_approve_once),
        approve_for_run=bool(args.external_approve_for_run),
        non_interactive=not bool(args.interactive),
    )
    if not approved:
        print("[blocked] company_web_research blocked by egress policy/approval gate.")
        return 3

    if provider and not api_key:
        print(f"[warn] no search key for provider '{provider['name']}' ({provider['api_key_env']}); crawl-only.")
    elif not provider:
        print("[warn] no search provider resolved (no key set); crawl-only.")

    payload = research_company(
        company=args.company,
        domain=args.domain,
        provider=provider,
        api_key=api_key,
        max_results=int(args.max_results),
        timeout=int(args.timeout),
        do_crawl=not bool(args.no_crawl),
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    cov = payload["coverage"]
    print(f"[ok] research -> {out_path} (sources={cov['source_count']}, domain_pages={cov['domain_page_count']}, web_search={cov['web_search_used']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
