import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import ig_api  # noqa: E402


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


def _env(monkeypatch):
    monkeypatch.setenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "IGUSER")
    monkeypatch.setenv("META_ACCESS_TOKEN", "TOKEN")


def test_create_story_item_posts_the_expected_payload(monkeypatch):
    _env(monkeypatch)
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return FakeResponse(200, {"id": "17999999999"})

    monkeypatch.setattr(ig_api, "_request", fake_request)

    cid = ig_api.create_story_item("https://pages.example/media/story/S1/slide_1.jpg")

    assert cid == "17999999999"
    assert len(calls) == 1
    method, url, kwargs = calls[0]
    assert method == "POST"
    assert url == f"{ig_api.GRAPH_HOST}/{ig_api.GRAPH_VERSION}/IGUSER/media"
    data = kwargs["data"]
    assert data["media_type"] == "STORIES"
    assert data["image_url"] == "https://pages.example/media/story/S1/slide_1.jpg"
    assert data["access_token"] == "TOKEN"
    # une story n'est pas un enfant de carrousel : pas de is_carousel_item
    assert "is_carousel_item" not in data


def test_create_story_item_raises_igapierror_on_meta_refusal(monkeypatch):
    _env(monkeypatch)

    def fake_request(method, url, **kwargs):
        return FakeResponse(400, {"error": {"message": "Unsupported media type"}})

    monkeypatch.setattr(ig_api, "_request", fake_request)

    with pytest.raises(ig_api.IgApiError):
        ig_api.create_story_item("https://pages.example/media/story/S1/slide_1.png")


def test_create_story_item_raises_when_response_has_no_id(monkeypatch):
    _env(monkeypatch)

    def fake_request(method, url, **kwargs):
        return FakeResponse(200, {})

    monkeypatch.setattr(ig_api, "_request", fake_request)

    with pytest.raises(ig_api.IgApiError):
        ig_api.create_story_item("https://pages.example/media/story/S1/slide_1.jpg")
