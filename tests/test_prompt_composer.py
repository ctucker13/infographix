from app.services.prompt_composer import PromptComposer


def test_prompt_contains_sections(preset_repo, planner, sample_user_input):
    composer = PromptComposer(preset_repo)
    spec = planner.plan(sample_user_input)
    prompt = composer.compose(spec)
    assert "Design a production-ready infographic." in prompt
    assert "process_flow" in prompt
    assert spec.sections[0].title in prompt
