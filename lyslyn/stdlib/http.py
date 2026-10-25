"""HTTP standard library module for Lyslyn."""
import urllib.request
import urllib.error
import urllib.parse
import json
from typing import Any, Dict, Optional
from ..values import LyslynHttpResponse, LyslynBuiltin


def request(method: str, url: str, options: Optional[Dict[str, Any]] = None) -> LyslynHttpResponse:
    options = options or {}
    method = method.upper()

    headers = options.get("headers", {}) or {}
    params = options.get("params", None)
    data = options.get("data", None)
    timeout = options.get("timeout", 30)

    # Append query params to URL if provided
    if params:
        url_parts = list(urllib.parse.urlparse(url))
        query = dict(urllib.parse.parse_qsl(url_parts[4]))
        query.update({k: str(v) for k, v in params.items()})
        url_parts[4] = urllib.parse.urlencode(query)
        url = urllib.parse.urlunparse(url_parts)

    body_bytes = None
    if data is not None:
        if isinstance(data, (dict, list)):
            body_bytes = json.dumps(data).encode("utf-8")
            if "Content-Type" not in headers and "content-type" not in headers:
                headers["Content-Type"] = "application/json"
        elif isinstance(data, str):
            body_bytes = data.encode("utf-8")
        elif isinstance(data, bytes):
            body_bytes = data
        else:
            body_bytes = str(data).encode("utf-8")

    req = urllib.request.Request(url, data=body_bytes, method=method)
    for k, v in headers.items():
        req.add_header(str(k), str(v))

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            resp_body = response.read().decode("utf-8", errors="replace")
            resp_headers = {k: v for k, v in response.getheaders()}
            return LyslynHttpResponse(status=status, body=resp_body, headers=resp_headers, url=url)
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8", errors="replace")
        resp_headers = {k: v for k, v in e.headers.items()}
        return LyslynHttpResponse(status=e.code, body=resp_body, headers=resp_headers, url=url)
    except Exception as e:
        raise RuntimeError(f"HTTP request to '{url}' failed: {e}")


def get(url: str, options: Optional[Dict[str, Any]] = None) -> LyslynHttpResponse:
    return request("GET", url, options)


def post(url: str, options: Optional[Dict[str, Any]] = None) -> LyslynHttpResponse:
    return request("POST", url, options)


def put(url: str, options: Optional[Dict[str, Any]] = None) -> LyslynHttpResponse:
    return request("PUT", url, options)


def delete(url: str, options: Optional[Dict[str, Any]] = None) -> LyslynHttpResponse:
    return request("DELETE", url, options)


def patch(url: str, options: Optional[Dict[str, Any]] = None) -> LyslynHttpResponse:
    return request("PATCH", url, options)


def export_module() -> Dict[str, Any]:
    return {
        "request": LyslynBuiltin("request", request),
        "get": LyslynBuiltin("get", get),
        "post": LyslynBuiltin("post", post),
        "put": LyslynBuiltin("put", put),
        "delete": LyslynBuiltin("delete", delete),
        "patch": LyslynBuiltin("patch", patch),
    }
