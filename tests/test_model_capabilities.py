from app.services.model_capabilities import get_capability, list_capabilities


def test_list_models_contains_two_entries():
    caps = list_capabilities()
    assert {cap.id for cap in caps} >= {"models/gemini-2.5-flash-image", "models/gemini-3.1-flash-image-preview"}


def test_capability_details():
    cap = get_capability("models/gemini-2.5-flash-image")
    assert cap.max_size == "2K"
    assert cap.supports_overlay is True
