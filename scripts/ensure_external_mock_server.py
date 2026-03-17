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
from urllib.parse import quote

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


def _find_mock_url(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("mockUrl", "url"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in payload.values():
            found = _find_mock_url(value)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_mock_url(item)
            if found:
                return found
    return ""


def _find_mock_id(payload: Any) -> str:
    if isinstance(payload, dict):
        value = payload.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
        for nested in payload.values():
            found = _find_mock_id(nested)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_mock_id(item)
            if found:
                return found
    return ""


def _extract_collection_id(payload: dict[str, Any]) -> str:
    candidates: list[str] = []
    collection = payload.get("collection")
    if isinstance(collection, dict):
        info = collection.get("info")
        if isinstance(info, dict):
            for key in ("_postman_id", "id", "uid"):
                value = info.get(key)
                if isinstance(value, str) and value.strip():
                    candidates.append(value.strip())
        for key in ("id", "uid"):
            value = collection.get(key)
            if isinstance(value, str) and value.strip():
                candidates.append(value.strip())
    for key in ("id", "uid"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            candidates.append(value.strip())
    return candidates[0] if candidates else ""


def _resolve_collection_id(base_url: str, api_key: str, token: str) -> str:
    value = token.strip()
    if not value:
        return ""
    try:
        payload = _http_json(
            "GET",
            f"{base_url}/collections/{quote(value, safe='')}",
            api_key=api_key,
        )
        resolved = _extract_collection_id(payload)
        return resolved or value
    except Exception:
        return value


def _normalize_base_path(base_path: str) -> str:
    value = base_path.strip()
    if not value:
        return ""
    return "/" + value.strip("/")


def _extract_mocks_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("mocks", "mockServers", "mockservers"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    if isinstance(payload.get("mock"), dict):
        return [payload["mock"]]
    if isinstance(payload.get("mockServer"), dict):
        return [payload["mockServer"]]
    found = _find_mock_node(payload)
    return [found] if isinstance(found, dict) else []


def _find_existing_mock_by_name(base_url: str, api_key: str, workspace_id: str, mock_name: str) -> dict[str, str] | None:
    candidates = [
        f"{base_url}/mocks?workspace={quote(workspace_id, safe='')}",
        f"{base_url}/mockservers?workspace={quote(workspace_id, safe='')}",
        f"{base_url}/mock-servers?workspace={quote(workspace_id, safe='')}",
    ]
    wanted = mock_name.strip().lower()
    for endpoint in candidates:
        try:
            payload = _http_json("GET", endpoint, api_key=api_key)
        except Exception:
            continue
        for item in _extract_mocks_list(payload):
            name = str(item.get("name", "")).strip().lower()
            if not name or name != wanted:
                continue
            mock_id = _find_mock_id(item)
            mock_url = _find_mock_url(item)
            if mock_id and mock_url:
                return {"mock_server_id": mock_id, "mock_url": mock_url}
    return None


def _resolve_postman_mock(args: argparse.Namespace) -> dict[str, str]:
    api_key = _read_env(args.postman_api_key_env, required=True)
    mock_server_id = _read_env(args.postman_mock_server_id_env, required=False)
    base_url = "https://api.getpostman.com"

    if mock_server_id:
        # Primary: current Postman endpoint /mocks/{id}. Fallback: legacy /mockservers/{id}.
        last_error: Exception | None = None
        for endpoint in (f"{base_url}/mocks/{quote(mock_server_id, safe='')}", f"{base_url}/mockservers/{quote(mock_server_id, safe='')}"):
            try:
                payload = _http_json("GET", endpoint, api_key=api_key)
                resolved_id = _find_mock_id(payload) or mock_server_id
                resolved_url = _find_mock_url(payload)
                if not resolved_url:
                    raise RuntimeError("mock URL is missing in Postman response")
                return {
                    "mock_server_id": resolved_id,
                    "mock_url": resolved_url,
                }
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue
        raise RuntimeError(f"Unable to resolve existing Postman mock server ID `{mock_server_id}`: {last_error}")

    workspace_id = _read_env(args.postman_workspace_id_env, required=True)
    try:
        _http_json(
            "GET",
            f"{base_url}/workspaces/{workspace_id}",
            api_key=api_key,
        )
    except RuntimeError as exc:
        raise RuntimeError(
            "Postman workspace preflight failed. "
            "Check POSTMAN_WORKSPACE_ID and ensure POSTMAN_API_KEY has access to that workspace. "
            f"Details: {exc}"
        ) from exc
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
    collection_id = _resolve_collection_id(base_url, api_key, collection_uid)

    mock_name = args.postman_mock_server_name.strip() or f"{args.project_slug}-docsops-mock"
    collection_tokens = [token for token in [collection_uid, collection_id] if token]
    if not collection_tokens:
        raise RuntimeError("Unable to resolve Postman collection token (uid/id) for mock creation.")

    last_error: Exception | None = None
    errors: list[str] = []

    # Try multiple endpoint + payload variations because Postman APIs changed across versions.
    create_candidates: list[tuple[str, str, dict[str, Any]]] = []
    for collection_token in collection_tokens:
        create_payload_primary: dict[str, Any] = {
            "mock": {
                "name": mock_name,
                "collection": collection_token,
                "private": bool(args.postman_private),
            }
        }
        create_payload_legacy: dict[str, Any] = {
            "mock": {
                "name": mock_name,
                "collection": collection_token,
                "private": bool(args.postman_private),
            },
            "workspace": {"id": workspace_id},
        }
        create_candidates.extend(
            [
                ("POST", f"{base_url}/mocks?workspace={quote(workspace_id, safe='')}", create_payload_primary),
                ("POST", f"{base_url}/mockservers", create_payload_legacy),
                ("POST", f"{base_url}/mock-servers", create_payload_legacy),
            ]
        )

    for method, endpoint, payload in create_candidates:
        try:
            created = _http_json(method, endpoint, api_key=api_key, payload=payload)
            resolved_id = _find_mock_id(created)
            resolved_url = _find_mock_url(created)
            if not resolved_id or not resolved_url:
                raise RuntimeError("created mock payload does not include id/url")
            return {
                "mock_server_id": resolved_id,
                "mock_url": resolved_url,
            }
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            errors.append(f"{endpoint}: {exc}")
            continue

    # If creation endpoints fail, try to reuse existing mock with the same generated name.
    existing = _find_existing_mock_by_name(base_url, api_key, workspace_id, mock_name)
    if existing:
        return existing

    detail = "; ".join(errors[-6:])
    raise RuntimeError(f"Unable to create or reuse Postman mock server: {last_error}. Attempts: {detail}")


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
