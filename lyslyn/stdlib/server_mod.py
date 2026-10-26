"""Production Multi-threaded HTTP Server & Routing engine for Lyslyn."""
import http.server
import json
import re
import socketserver
import time
import urllib.parse
from typing import Any, Callable, Dict, List, Optional, Tuple
from ..values import LyslynBuiltin


class RequestContext:
    """Represents an incoming HTTP request in Lyslyn server."""
    def __init__(
        self,
        method: str,
        path: str,
        params: Dict[str, str],
        query: Dict[str, str],
        headers: Dict[str, str],
        body: Any,
        ip: str
    ):
        self.method = method
        self.path = path
        self.params = params
        self.query = query
        self.headers = headers
        self.body = body
        self.ip = ip

    def __repr__(self) -> str:
        return f"<Request {self.method} {self.path}>"


class RouteEntry:
    def __init__(self, method: str, path_pattern: str, handler: Any):
        self.method = method.upper()
        self.path_pattern = path_pattern
        self.handler = handler
        self.param_names: List[str] = []
        self.regex = self._compile_pattern(path_pattern)

    def _compile_pattern(self, pattern: str) -> re.Pattern:
        # Convert e.g. "/api/users/:id/posts/:post_id" to regex
        parts = pattern.strip("/").split("/") if pattern.strip("/") else []
        regex_parts = []
        for part in parts:
            if part.startswith(":"):
                param_name = part[1:]
                self.param_names.append(param_name)
                regex_parts.append(r"([^/]+)")
            elif part == "*":
                regex_parts.append(r"(.*)")
            else:
                regex_parts.append(re.escape(part))
        full_regex = "^/" + "/".join(regex_parts) + "/?$"
        if not parts:
            full_regex = "^/?$"
        return re.compile(full_regex)

    def match(self, method: str, path: str) -> Optional[Dict[str, str]]:
        if self.method != "*" and self.method != method.upper():
            return None
        clean_path = urllib.parse.urlparse(path).path
        m = self.regex.match(clean_path)
        if not m:
            return None
        params = {}
        for name, val in zip(self.param_names, m.groups()):
            params[name] = urllib.parse.unquote(val)
        return params


class ServerApp:
    def __init__(self):
        self.routes: List[RouteEntry] = []
        self.middlewares: List[Callable] = []
        self.http_server: Optional[http.server.ThreadingHTTPServer] = None
        self.is_running = False

    def use(self, middleware: Callable) -> "ServerApp":
        self.middlewares.append(middleware)
        return self

    def add_route(self, method: str, path: str, handler: Any) -> "ServerApp":
        self.routes.append(RouteEntry(method, path, handler))
        return self

    def get(self, path: str, handler: Any) -> "ServerApp":
        return self.add_route("GET", path, handler)

    def post(self, path: str, handler: Any) -> "ServerApp":
        return self.add_route("POST", path, handler)

    def put(self, path: str, handler: Any) -> "ServerApp":
        return self.add_route("PUT", path, handler)

    def delete(self, path: str, handler: Any) -> "ServerApp":
        return self.add_route("DELETE", path, handler)

    def patch(self, path: str, handler: Any) -> "ServerApp":
        return self.add_route("PATCH", path, handler)

    def dispatch_request(self, method: str, raw_url: str, headers: Dict[str, str], raw_body: str, client_ip: str) -> Tuple[int, Dict[str, str], str]:
        parsed = urllib.parse.urlparse(raw_url)
        path = parsed.path
        query = {k: v[0] if len(v) == 1 else v for k, v in urllib.parse.parse_qs(parsed.query).items()}

        # Parse body
        body = None
        if raw_body:
            content_type = headers.get("content-type", "")
            if "application/json" in content_type or raw_body.strip().startswith(("{", "[")):
                try:
                    body = json.loads(raw_body)
                except Exception:
                    body = raw_body
            else:
                body = raw_body

        req = RequestContext(
            method=method,
            path=path,
            params={},
            query=query,
            headers=headers,
            body=body,
            ip=client_ip
        )

        resp_headers = {"Content-Type": "application/json"}

        # Execute middlewares
        for mid in self.middlewares:
            if callable(mid):
                try:
                    res = mid(req)
                    # If middleware returns a dict with status or early response
                    if isinstance(res, dict) and "status" in res:
                        body_out = json.dumps(res.get("body", {}))
                        return res.get("status", 200), resp_headers, body_out
                except Exception as e:
                    return 500, resp_headers, json.dumps({"error": f"Middleware error: {e}"})

        # Match routes
        for route in self.routes:
            params = route.match(method, path)
            if params is not None:
                req.params = params
                try:
                    # Invoke handler
                    if callable(route.handler):
                        result = route.handler(req)
                    else:
                        result = route.handler

                    status = 200
                    payload = result
                    if isinstance(result, tuple) and len(result) >= 2:
                        status = int(result[0])
                        payload = result[1]
                    elif isinstance(result, dict) and "_status" in result:
                        status = int(result.pop("_status"))
                        payload = result

                    if isinstance(payload, (dict, list)):
                        body_str = json.dumps(payload)
                        resp_headers["Content-Type"] = "application/json"
                    elif isinstance(payload, str):
                        body_str = payload
                        if not any(k.lower() == "content-type" for k in resp_headers):
                            resp_headers["Content-Type"] = "text/plain"
                    else:
                        body_str = str(payload)

                    return status, resp_headers, body_str

                except Exception as e:
                    return 500, resp_headers, json.dumps({"error": f"Internal Server Error: {e}"})

        # Not found
        return 404, resp_headers, json.dumps({
            "error": "Not Found",
            "message": f"Cannot {method} {path}"
        })

    def listen(self, port: int, host: str = "0.0.0.0", blocking: bool = True) -> None:
        port = int(port)
        host = str(host)
        app = self

        class ThreadedHandler(http.server.BaseHTTPRequestHandler):
            def handle_one_request(self):
                try:
                    super().handle_one_request()
                except (ConnectionResetError, BrokenPipeError):
                    pass

            def do_request(self, method: str):
                length = int(self.headers.get("content-length", 0))
                raw_body = self.rfile.read(length).decode("utf-8", errors="replace") if length > 0 else ""
                headers_dict = {k.lower(): v for k, v in self.headers.items()}
                client_ip = self.client_address[0]

                status, out_headers, out_body = app.dispatch_request(
                    method=method,
                    raw_url=self.path,
                    headers=headers_dict,
                    raw_body=raw_body,
                    client_ip=client_ip
                )

                try:
                    self.send_response(status)
                    for hk, hv in out_headers.items():
                        self.send_header(hk, hv)
                    out_bytes = out_body.encode("utf-8")
                    self.send_header("Content-Length", str(len(out_bytes)))
                    self.end_headers()
                    self.wfile.write(out_bytes)
                except (ConnectionResetError, BrokenPipeError):
                    pass

            def do_GET(self):
                self.do_request("GET")

            def do_POST(self):
                self.do_request("POST")

            def do_PUT(self):
                self.do_request("PUT")

            def do_DELETE(self):
                self.do_request("DELETE")

            def do_PATCH(self):
                self.do_request("PATCH")

            def do_OPTIONS(self):
                # Built-in preflight handling
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
                self.end_headers()

            def log_message(self, format, *args):
                pass  # Use Lyslyn's custom logger middleware instead

        self.http_server = http.server.ThreadingHTTPServer((host, port), ThreadedHandler)
        self.is_running = True
        display_host = "127.0.0.1" if host == "0.0.0.0" else host
        print(f"\033[92m●\033[0m \033[1mLyslyn HTTP Server\033[0m listening on \033[96mhttp://{display_host}:{port}\033[0m")

        if blocking:
            try:
                self.http_server.serve_forever()
            except KeyboardInterrupt:
                self.close()

    def close(self) -> None:
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()
            self.is_running = False


# ============================================================================
# Built-in Middleware Creators
# ============================================================================

def middleware_cors(allowed_origins: str = "*") -> Callable:
    def _cors(req: RequestContext) -> None:
        # Handled in responses
        return None
    return _cors


def middleware_logger() -> Callable:
    def _logger(req: RequestContext) -> None:
        print(f"\033[94m[{req.method}]\033[0m {req.path} - from {req.ip}")
        return None
    return _logger


def middleware_auth_bearer(expected_token: str) -> Callable:
    def _auth(req: RequestContext) -> Optional[Dict[str, Any]]:
        auth_header = req.headers.get("authorization", "")
        if not auth_header.startswith("Bearer ") or auth_header[7:].strip() != expected_token:
            return {
                "status": 401,
                "body": {"error": "Unauthorized", "message": "Invalid or missing Bearer token"}
            }
        return None
    return _auth


def export_module() -> Dict[str, Any]:
    return {
        "create": LyslynBuiltin("create", lambda: ServerApp(), arity=0),
        "cors": LyslynBuiltin("cors", middleware_cors),
        "logger": LyslynBuiltin("logger", middleware_logger, arity=0),
        "auth_bearer": LyslynBuiltin("auth_bearer", middleware_auth_bearer, arity=1),
    }
