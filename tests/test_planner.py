from app.models.specs import InfographicSection, RenderingMode, TextBlock, UserInput


def test_planner_returns_spec(planner, sample_user_input):
    spec = planner.plan(sample_user_input)
    assert spec.infographic_type == sample_user_input.infographic_type
    assert spec.aspect_ratio == sample_user_input.aspect_ratio
    assert spec.rendering_mode in (RenderingMode.PURE_IMAGE, RenderingMode.HYBRID_OVERLAY)


def test_planner_recommends_hybrid_for_exact_text(planner):
    heavy_section = InfographicSection(
        id="dense",
        title="Dense",
        text_blocks=[
            TextBlock(label="Paragraph", body=" ".join(["word"] * 500), exact_text=True),
        ],
    )
    user_input = UserInput(
        request_id="req-dense",
        topic="Legal Terms",
        audience="law",
        desired_model="models/gemini-2.5-flash-image",
        infographic_type="process_flow",
        visual_style="flat_vector",
        sections=[heavy_section],
        exact_text_required=True,
    )
    spec = planner.plan(user_input)
    assert spec.rendering_mode == RenderingMode.HYBRID_OVERLAY
    assert spec.recommended_model == "models/gemini-3.1-flash-image-preview"
