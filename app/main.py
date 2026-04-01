from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.db import init_db
from app.models.presets import PresetRepository
from app.routers import api, ui
from app.services.gemini_client import GeminiImageClient
from app.services.text_client import GeminiTextClient
from app.services.markdown_renderer import render_markdown
from app.services.planner import InfographicPlanner
from app.services.prompt_composer import PromptComposer

settings = get_settings()
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["markdown"] = render_markdown

style_dir = Path("presets/styles")
infographic_dir = Path("presets/infographics")
section_template_dir = Path("presets/section_templates")
preset_repo = PresetRepository(
    style_dir=style_dir,
    infographic_dir=infographic_dir,
    section_template_dir=section_template_dir,
)
preset_repo.load()

planner = InfographicPlanner(preset_repo)
composer = PromptComposer(preset_repo)

gemini_client = GeminiImageClient()
gemini_text_client = GeminiTextClient()

app = FastAPI(title="Infographix", version="0.1.0")
app.state.settings = settings
app.state.preset_repo = preset_repo
app.state.planner = planner
app.state.prompt_composer = composer
app.state.gemini_client = gemini_client
app.state.gemini_text_client = gemini_text_client
app.state.templates = templates

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/storage", StaticFiles(directory=settings.storage_path), name="storage")
app.include_router(api.router)
app.include_router(ui.router)


@app.on_event("startup")
async def startup_event() -> None:
    await init_db()
