"""Restricted JSON-RPC client. Never retries a potentially paid RPC call."""

import ipaddress
import json
from urllib.parse import urlparse

import httpx


class RPCError(RuntimeError):
    def __init__(self, message: str, *, code: int | None = None, not_found: bool = False):
        super().__init__(message)
        self.code = code
        self.not_found = not_found


class RPC:
    def __init__(self, url: str, auth: tuple[str, str] | None = None):
        parsed = urlparse(url)
        try:
            local = ipaddress.ip_address(parsed.hostname or "").is_loopback
        except ValueError:
            local = False
        if (
            not local
            or parsed.scheme != "http"
            or parsed.username
            or parsed.password
            or parsed.path != "/json_rpc"
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Wallet RPC requires an explicit loopback IP and /json_rpc")
        self.url = url
        self.auth = auth

    def call(self, method: str, params: dict | None = None) -> dict:
        request = {"jsonrpc": "2.0", "id": "dero-chat", "method": method}
        if params is not None:
            request["params"] = params
        try:
            with httpx.Client(timeout=30, trust_env=False, follow_redirects=False) as client:
                with client.stream(
                    "POST",
                    self.url,
                    auth=self.auth,
                    json=request,
                ) as response:
                    response.raise_for_status()
                    content = bytearray()
                    for chunk in response.iter_bytes():
                        content.extend(chunk)
                        if len(content) > 32 * 1024 * 1024:
                            raise RPCError("Wallet RPC response exceeds local limit")
                    data = json.loads(content)
        except httpx.HTTPStatusError as exc:
            raise RPCError(f"Wallet RPC HTTP status {exc.response.status_code}") from None
        except httpx.HTTPError as exc:
            raise RPCError(f"Wallet RPC transport failure: {type(exc).__name__}") from None
        except ValueError:
            raise RPCError("Wallet RPC returned invalid JSON") from None
        if not isinstance(data, dict) or data.get("id") != "dero-chat":
            raise RPCError("Wallet RPC response ID or structure is invalid")
        if data.get("error"):
            error = data["error"]
            code = error.get("code") if isinstance(error, dict) else None
            message = error.get("message", "") if isinstance(error, dict) else ""
            missing = isinstance(message, str) and "Transaction not found." in message
            raise RPCError(f"Wallet RPC error code {code}", code=code, not_found=missing)
        if not isinstance(data.get("result"), dict):
            raise RPCError("Wallet RPC result is invalid")
        return data["result"]
