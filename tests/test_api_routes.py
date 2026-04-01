import uuid


def _payload() -> dict:
    return {
        "request_id": f"req-{uuid.uuid4()}",
        "topic": "API Testing",
        "audience": "developers",
        "desired_model": "models/gemini-2.5-flash-image",
        "infographic_type": "process_flow",
        "visual_style": "flat_vector",
        "title": "API Flow",
        "sections": [
            {
                "id": "step1",
                "title": "Step 1",
                "text_blocks": [
                    {"label": "Action", "body": "Call endpoint", "exact_text": False}
                ],
            }
        ],
    }


def test_models_endpoint(client):
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert any(model["id"] == "models/gemini-2.5-flash-image" for model in data)


def test_section_templates_endpoint(client):
    response = client.get("/api/section-templates")
    assert response.status_code == 200
    payload = response.json()
    assert "section_templates" in payload
    assert any(tpl["id"] == "process_three_step" for tpl in payload["section_templates"])


def test_spec_preview_endpoint(client):
    response = client.post("/api/spec/preview", json=_payload())
    assert response.status_code == 200
    data = response.json()
    assert data["spec"]["infographic_type"] == "process_flow"


def test_render_and_history_flow(client):
    render_response = client.post("/api/render", json=_payload())
    assert render_response.status_code == 200
    body = render_response.json()
    assert body["image_path"].startswith("/storage/")
    generation_id = body["generation_id"]

    history_item = client.get(f"/api/history/{generation_id}")
    assert history_item.status_code == 200
    history_data = history_item.json()
    assert history_data["id"] == generation_id


def test_render_handles_gemini_failure(client, mock_gemini):
    mock_gemini.side_effect = RuntimeError("Gemini offline")
    response = client.post("/api/render", json=_payload())
    assert response.status_code == 503
    data = response.json()
    assert "Gemini offline" in data["detail"]
