import json

from src.watermark_service import InfraiClient, publish_creator_image


class FakeResponse:
    status = 200

    def __init__(self, data):
        self.data = json.dumps({"ok": True, "data": data}).encode()

    def read(self):
        return self.data


def test_publish_adds_creator_mark_and_subscriber_state():
    calls = []

    def opener(request):
        calls.append((request.full_url, json.loads(request.data), request.headers["X-idempotency-key"]))
        if request.full_url.endswith("/upload"):
            return FakeResponse({"id": "img_123"})
        return FakeResponse({"id": "processed_123", "url": "https://cdn.example/processed.jpg"})

    result = publish_creator_image(b"pixels", "post.jpg", "monthly supporters", InfraiClient("test", opener))

    assert result["state"] == "published"
    assert result["subscriber"] == "monthly supporters"
    assert calls[0][0].endswith("/v1/image/upload")
    assert set(calls[1][1]) == {"image", "ops"}
    assert calls[1][1]["image"] == "img_123"
    assert calls[1][1]["ops"] == [
        {
            "type": "watermark",
            "text": "(c) monthly supporters",
            "position": "bottom_right",
            "opacity": 0.65,
        }
    ]
