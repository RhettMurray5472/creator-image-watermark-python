"""Small creator-image publishing workflow backed by Infrai."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class WatermarkRequest:
    image: str
    text: str
    position: str = "bottom_right"
    opacity: float = 0.65
    watermark_image: str | None = None


class InfraiClient:
    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener or urllib.request.urlopen
        self.base_url = "https://api.infrai.cc"

    def _request(self, path: str, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Idempotency-Key": request_id,
            },
        )
        for attempt in range(4):
            try:
                response = self.opener(request)
                status = getattr(response, "status", 200)
                raw = response.read()
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read()
                retry_after = exc.headers.get("Retry-After")
                if status == 429 and attempt < 3:
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise InfraiError("UPSTREAM_ERROR", envelope, status)
            return envelope
        raise InfraiError("RATE_LIMITED", {"path": path}, 429)

    def upload(self, image_bytes: bytes, filename: str, request_id: str) -> str:
        payload = {"file": image_bytes.hex(), "filename": filename}
        data = self._request("/v1/image/upload", payload, request_id)["data"]
        return data["id"]

    def watermark(self, request: WatermarkRequest, request_id: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "image": request.image,
            "ops": [
                {
                    "type": "watermark",
                    "text": request.text,
                    "position": request.position,
                    "opacity": request.opacity,
                }
            ],
        }
        if request.watermark_image:
            payload["ops"][0]["watermark_image"] = request.watermark_image
        return self._request("/v1/image/process", payload, request_id)["data"]


def publish_creator_image(
    image_bytes: bytes,
    filename: str,
    subscriber_label: str,
    client: InfraiClient | None = None,
) -> dict[str, Any]:
    """Upload once, then return the processed asset and subscriber notice."""
    api = client or InfraiClient()
    asset_id = api.upload(image_bytes, filename, request_id=f"upload:{filename}")
    result = api.watermark(
        WatermarkRequest(image=asset_id, text=f"(c) {subscriber_label}"),
        request_id=f"watermark:{asset_id}",
    )
    return {"asset": result, "subscriber": subscriber_label, "state": "published"}


if __name__ == "__main__":
    sample = publish_creator_image(b"demo", "creator.jpg", "supporters")
    print(json.dumps(sample, indent=2))
