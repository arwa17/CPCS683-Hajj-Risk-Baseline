"""Google Gemini API backend for the single-agent Hajj risk baseline."""
from __future__ import annotations

import json
import os
from urllib import error, request
from urllib.parse import quote


class ProviderError(RuntimeError):
    pass


class LLMProvider:
    def __init__(
        self, model: str = "gemini-3.1-flash-lite",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout: int = 120, api_key: str | None = None,
        seed: int | None = None,
    ):
        self.backend = "gemini"
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        raw_seed = os.getenv("HAJJ_SEED", "42") if seed is None else seed
        try:
            if isinstance(raw_seed, bool):
                raise ValueError("boolean is not a valid seed")
            self.seed = int(raw_seed)
            if not 0 <= self.seed <= 2147483647:
                raise ValueError("seed is out of range")
        except (ValueError, TypeError) as exc:
            raise ProviderError("HAJJ_SEED must be an integer between 0 and 2147483647.") from exc
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ProviderError(
                "GEMINI_API_KEY is missing. Create a key in Google AI Studio and set it in your terminal."
            )

    def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, dict]:
        url = self.base_url + "/models/" + quote(self.model, safe="-_.") + ":generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0,
                "seed": self.seed,
                "responseMimeType": "application/json",
            },
        }
        req = request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            parts = data["candidates"][0]["content"]["parts"]
            content = "".join(
                part["text"] for part in parts
                if isinstance(part, dict)
                and isinstance(part.get("text"), str)
                and not part.get("thought", False)
            )
            if not content.strip():
                raise ValueError("Model response was empty.")
            usage_data = data.get("usageMetadata") or {}
            return content, {
                "input_tokens": usage_data.get("promptTokenCount"),
                "output_tokens": usage_data.get("candidatesTokenCount"),
            }
        except error.HTTPError as exc:
            detail = exc.read(250).decode("utf-8", errors="replace")
            raise ProviderError(f"Gemini returned HTTP {exc.code}: {detail}") from exc
        except (error.URLError, OSError, TimeoutError) as exc:
            raise ProviderError(f"Cannot reach Gemini: {exc}") from exc
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            raise ProviderError(f"Invalid Gemini response: {exc}") from exc
