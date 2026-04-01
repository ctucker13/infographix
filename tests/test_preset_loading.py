from pathlib import Path

from app.models.presets import PresetRepository


def test_presets_load_all_styles_and_infographics():
    base = Path(__file__).resolve().parents[1]
    repo = PresetRepository(
        base / "presets" / "styles",
        base / "presets" / "infographics",
        base / "presets" / "section_templates",
    )
    repo.load()
    assert "pixel_art_16bit" in repo.styles
    assert "process_flow" in repo.infographics
    assert len(repo.styles) >= 10
    assert len(repo.infographics) >= 12
    assert "process_three_step" in repo.section_templates
    assert len(repo.section_templates) >= 3
