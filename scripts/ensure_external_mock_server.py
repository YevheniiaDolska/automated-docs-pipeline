#!/usr/bin/env python3
"""Ensure external mock server exists and return resolved mock_base_url.

Initial provider: Postman API.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib import error, request

import yaml


def _read_env(name: str, *, required: bool) -> str:
    value = os.environ.get(name, "").strip()
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _http_json(
    method: str,
    url: str,
    *,
    api_key: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = None
    headers = {
        "X-Api-Key": api_key,
        "Accept": "application/json",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url=url, data=body, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        response_text = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"HTTP {exc.code} while calling {url}: {response_text or exc.reason}"
        ) from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error while calling {url}: {exc.reason}") from exc

    data = json.loads(raw or "{}")
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected JSON response from {url}")
    return data


def _find_mock_node(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, dict):
        if isinstance(payload.get("id"), str) and isinstance(payload.get("url"), str):
            return payload
        for value in payload.values():
            found = _find_mock_node(value)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_mock_node(item)
            if found is not None:
                return found
    return None


def _normalize_base_path(base_path: str) -> str:
    value = base_path.strip()
    if not value:
        return ""
    return "/" + value.strip("/")


def _resolve_postman_mock(args: argparse.Namespace) -> dict[str, str]:
    api_key = _read_env(args.postman_api_key_env, required=True)
    mock_server_id = _read_env(args.postman_mock_server_id_env, required=False)
    base_url = "https://api.getpostman.com"

    if mock_server_id:
        payload = _http_json(
            "GET",
            f"{base_url}/mockservers/{mock_server_id}",
            api_key=api_key,
        )
        node = _find_mock_node(payload)
        if node is None:
            raise RuntimeError("Unable to find mock server fields (id/url) in Postman response.")
        return {
            "mock_server_id": str(node["id"]),
            "mock_url": str(node["url"]),
        }

    workspace_id = _read_env(args.postman_workspace_id_env, required=True)
    collection_uid = _read_env(args.postman_collection_uid_env, required=False)
    if not collection_uid:
        if not args.spec_path:
            raise RuntimeError(
                "POSTMAN_COLLECTION_UID is not set and --spec-path is missing. "
                "Provide collection UID or pass generated OpenAPI spec path."
            )
        spec_file = Path(args.spec_path)
        if not spec_file.exists():
            raise RuntimeError(f"Spec file for Postman import not found: {spec_file}")
        spec_obj = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
        import_payload = {
            "type": "json",
            "input": spec_obj,
        }
        imported = _http_json(
            "POST",
            f"{base_url}/import/openapi",
            api_key=api_key,
            payload=import_payload,
        )
        collection_uid = str(
            (imported.get("collections") or [{}])[0].get("uid", "")
        ).strip()
        if not collection_uid:
            found = _find_mock_node(imported)
            if found is not None:
                collection_uid = str(found.get("uid", "")).strip()
        if not collection_uid:
            raise RuntimeError("Unable to resolve collection UID from Postman import response.")
    mock_name = args.postman_mock_server_name.strip() or f"{args.project_slug}-docsops-mock"
    create_payload: dict[str, Any] = {
        "mock": {
            "name": mock_name,
            "collection": collection_uid,
            "private": bool(args.postman_private),
        },
        "workspace": {"id": workspace_id},
    }
    created = _http_json(
        "POST",
        f"{base_url}/mockservers",
        api_key=api_key,
        payload=create_payload,
    )
    node = _find_mock_node(created)
    if node is None:
        raise RuntimeError("Unable to parse created Postman mock server response.")
    return {
        "mock_server_id": str(node["id"]),
        "mock_url": str(node["url"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure external mock server and resolve mock_base_url")
    parser.add_argument("--provider", default="postman")
    parser.add_argument("--project-slug", required=True)
    parser.add_argument("--base-path", default="/v1")
    parser.add_argument("--spec-path", default="")
    parser.add_argument("--output-json", default="")

    parser.add_argument("--postman-api-key-env", default="POSTMAN_API_KEY")
    parser.add_argument("--postman-workspace-id-env", default="POSTMAN_WORKSPACE_ID")
    parser.add_argument("--postman-collection-uid-env", default="POSTMAN_COLLECTION_UID")
    parser.add_argument("--postman-mock-server-id-env", default="POSTMAN_MOCK_SERVER_ID")
    parser.add_argument("--postman-mock-server-name", default="")
    parser.add_argument("--postman-private", action="store_true")
    args = parser.parse_args()

    provider = args.provider.strip().lower()
    if provider != "postman":
        raise RuntimeError(f"Unsupported external mock provider: {provider}")

    resolved = _resolve_postman_mock(args)
    base_path = _normalize_base_path(args.base_path)
    mock_base_url = resolved["mock_url"].rstrip("/") + base_path

    output_payload = {
        "provider": provider,
        "project_slug": args.project_slug,
        "mock_server_id": resolved["mock_server_id"],
        "mock_url": resolved["mock_url"],
        "mock_base_url": mock_base_url,
    }

    if args.output_json:
        out = Path(args.output_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(output_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(output_payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
