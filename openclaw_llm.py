"""
OpenClaw LLM Client - Routes all LLM calls through OpenClaw Gateway

Uses the OpenClaw Gateway's built-in HTTP endpoint (OpenAI-compatible
chat completions API at /v1/chat/completions) to access configured models.

Gateway info (from OpenClaw config):
  - Local address: http://127.0.0.1:18789
  - Auth: token-based
  - Endpoint: /v1/chat/completions (must be enabled in gateway config)
"""

import json
import urllib.request
import urllib.error
import urllib.parse
import time
import os
import re
from typing import Optional, Generator, Any


class OpenClawLLM:
    """Client for OpenClaw Gateway LLM API."""

    def __init__(
        self,
        gateway_url: str = "http://127.0.0.1:18789",
        token: Optional[str] = None,
        model: str = "openclaw",
        timeout: int = 300,
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.token = token or self._get_token_from_env()
        self.model = model
        self.timeout = timeout

    def _get_token_from_env(self) -> str:
        """Try to read token from OPENCLAW_TOKEN env var."""
        return os.environ.get("OPENCLAW_TOKEN", "")

    def _make_request(
        self,
        messages: list,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> urllib.request.Request:
        """Build the chat completions request."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.gateway_url}/v1/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            method="POST",
        )
        return req

    def _parse_sse_stream(self, response) -> Generator[str, None, None]:
        """Parse Server-Sent Events stream from OpenAI-compatible endpoint."""
        buffer = ""
        for line in response:
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="replace")
            if not line:
                continue
            if line.startswith("data: "):
                data = line[6:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    # OpenAI-compatible chunk format
                    delta = None
                    if "choices" in obj:
                        delta = obj["choices"][0].get("delta", {})
                    elif "message" in obj:
                        delta = obj.get("message", {})
                    content = delta.get("content") or delta.get("text") or ""
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue
        # Also handle non-SSE responses (concatenated JSON objects separated by newlines)
        # These come from some providers as plain lines
        # Already handled above via data: prefix check

    def complete(
        self,
        prompt: str,
        system: str = "",
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> dict:
        """
        Send a completion request and return the full response.

        Args:
            prompt: User prompt text
            system: Optional system message
            stream: Whether to use streaming
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            dict with keys: text (str), usage (dict), raw (dict)
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        req = self._make_request(messages, stream=False, temperature=temperature, max_tokens=max_tokens)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                text = ""
                if "choices" in raw:
                    text = raw["choices"][0]["message"]["content"]
                return {"text": text, "usage": raw.get("usage", {}), "raw": raw}
        except Exception as e:
            return {"text": "", "usage": {}, "error": str(e)}

    def complete_stream(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> Generator[str, None, None]:
        """
        Send a streaming completion request and yield tokens.

        Yields:
            str: Tokens as they arrive
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        req = self._make_request(messages, stream=True, temperature=temperature, max_tokens=max_tokens)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                for line in resp:
                    if isinstance(line, bytes):
                        line = line.decode("utf-8", errors="replace")
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                        if "choices" in obj:
                            delta = obj["choices"][0].get("delta", {})
                            content = delta.get("content") or delta.get("text") or ""
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            yield f"[ERROR: {e}]"

    def complete_raw(
        self,
        messages: list,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> dict:
        """
        Send a raw messages array (for conversation-style calls).

        Args:
            messages: List of {"role": ..., "content": ...} dicts
            stream: Whether to stream
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            dict with keys: text (str), usage (dict), raw (dict), error (str)
        """
        req = self._make_request(messages, stream=False, temperature=temperature, max_tokens=max_tokens)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                text = ""
                if "choices" in raw:
                    text = raw["choices"][0]["message"]["content"]
                return {"text": text, "usage": raw.get("usage", {}), "raw": raw}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            return {"text": "", "usage": {}, "error": f"HTTP {e.code}: {e.reason}", "body": body[:500]}
        except Exception as e:
            return {"text": "", "usage": {}, "error": str(e)}

    def stream_raw(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> Generator[str, None, None]:
        """
        Stream a raw messages array.
        """
        req = self._make_request(messages, stream=True, temperature=temperature, max_tokens=max_tokens)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                for line in resp:
                    if isinstance(line, bytes):
                        line = line.decode("utf-8", errors="replace")
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                        if "choices" in obj:
                            delta = obj["choices"][0].get("delta", {})
                            content = delta.get("content") or delta.get("text") or ""
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            yield f"[ERROR: {e}]"


def get_token_from_gateway() -> str:
    """Try to read the OpenClaw gateway token from config file."""
    import pathlib

    config_path = pathlib.Path.home() / ".openclaw" / "openclaw.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                raw = f.read()
                m = re.search(r'"token"\s*:\s*"([^"]+)"', raw)
                if m:
                    return m.group(1)
        except Exception:
            pass
    return os.environ.get("OPENCLAW_TOKEN", "")


# Singleton instance
_default_client: Optional[OpenClawLLM] = None


def get_default_client() -> OpenClawLLM:
    global _default_client
    if _default_client is None:
        _default_client = OpenClawLLM(token=get_token_from_gateway())
    return _default_client


def complete(prompt: str, system: str = "", **kwargs) -> dict:
    """Convenience function for one-shot completion."""
    return get_default_client().complete(prompt, system=system, **kwargs)


def stream_complete(prompt: str, system: str = "", **kwargs) -> Generator[str, None, None]:
    """Convenience function for streaming completion."""
    return get_default_client().complete_stream(prompt, system=system, **kwargs)


def complete_messages(messages: list, **kwargs) -> dict:
    """Convenience function for raw message-based completion."""
    return get_default_client().complete_raw(messages, **kwargs)


def stream_complete_messages(messages: list, **kwargs) -> Generator[str, None, None]:
    """Convenience function for streaming raw message-based completion."""
    return get_default_client().stream_raw(messages, **kwargs)