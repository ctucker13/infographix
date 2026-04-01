from __future__ import annotations

import os
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_infographix.db")

from app.main import app  # noqa: E402
from app.models.presets import PresetRepository
from app.models.specs import InfographicSection, TextBlock, UserInput
from app.services.gemini_client import ImageRenderResult
from app.services.planner import InfographicPlanner


@pytest.fixture(scope="session")
def preset_repo() -> PresetRepository:
    base = Path(__file__).resolve().parents[1]
    repo = PresetRepository(
        base / "presets" / "styles",
        base / "presets" / "infographics",
        base / "presets" / "section_templates",
    )
    repo.load()
    return repo


@pytest.fixture(scope="session")
def planner(preset_repo: PresetRepository) -> InfographicPlanner:
    return InfographicPlanner(preset_repo)


@pytest.fixture()
def sample_sections() -> List[InfographicSection]:
    return [
        InfographicSection(
            id="intro",
            title="Introduction",
            text_blocks=[TextBlock(label="Summary", body="Explain basics", exact_text=False)],
        ),
        InfographicSection(
            id="insight",
            title="Key Insight",
            text_blocks=[TextBlock(label="Detail", body="Key metric and note", exact_text=True)],
        ),
    ]


@pytest.fixture()
def sample_user_input(sample_sections: List[InfographicSection]) -> UserInput:
    return UserInput(
        request_id="req-test",
        topic="Sample Topic",
        audience="designers",
        desired_model="models/gemini-2.5-flash-image",
        infographic_type="process_flow",
        visual_style="flat_vector",
        title="Testing",
        subtitle="Pipeline",
        sections=sample_sections,
        footer_text="Source: internal",
        aspect_ratio="4:5",
        image_size="1024x1024",
        exact_text_required=False,
        text_preference="summarize",
    )


@pytest.fixture()
def mock_gemini(monkeypatch) -> AsyncMock:
    from app.main import gemini_client

    mock = AsyncMock(
        return_value=ImageRenderResult(
            image_path="/storage/outputs/test.png",
            model="mock-model",
            prompt="mock-prompt",
        )
    )
    monkeypatch.setattr(gemini_client, "generate_image", mock)
    return mock


@pytest.fixture()
def client(mock_gemini: AsyncMock) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
