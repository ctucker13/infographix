from app.models.specs import InfographicSection, InfographicSpec, TextBlock
from app.services.text_budget import evaluate_text_budget


def _base_spec() -> InfographicSpec:
    return InfographicSpec(
        request_id="req",
        topic="Energy",
        audience="executives",
        selected_model="models/gemini-2.5-flash-image",
        recommended_model="models/gemini-2.5-flash-image",
        infographic_type="process_flow",
        visual_style="flat_vector",
        sections=[
            InfographicSection(
                id="intro",
                title="Intro",
                text_blocks=[TextBlock(label="A", body="Short info", exact_text=False)],
            )
        ],
    )


def test_text_budget_within_limits():
    spec = _base_spec()
    status, warnings, density = evaluate_text_budget(spec)
    assert status.value == "within_limits"
    assert warnings == []
    assert density.value in {"light", "balanced"}


def test_text_budget_over_limit():
    spec = _base_spec()
    spec.sections[0].text_blocks = [TextBlock(label="A", body="Long " * 100, exact_text=False)] * 6
    status, warnings, density = evaluate_text_budget(spec)
    assert status.value != "within_limits"
    assert warnings
    assert density.value == "heavy"
