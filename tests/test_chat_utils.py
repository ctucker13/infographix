from app.routers.ui import _format_size
from app.services.text_client import _estimate_visual_score


def test_format_size_units():
    assert _format_size(512) == "512B"
    assert _format_size(2048).endswith("KB")
    assert _format_size(5 * 1024 * 1024).endswith("MB")


def test_estimate_visual_score_prefers_image_keywords():
    score = _estimate_visual_score("Please draw an infographic of our roadmap", [])
    assert score >= 1


def test_estimate_visual_score_penalizes_text_requests():
    score = _estimate_visual_score("Summarize these notes for our meeting", [])
    assert score <= 0
