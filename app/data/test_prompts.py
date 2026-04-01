from __future__ import annotations

from typing import Any, Dict


TEST_PROMPTS: Dict[str, Dict[str, Any]] = {
    "comparison_chart": {
        "topic": "EV fleet vs diesel vans",
        "audience": "Stakeholder show-and-tell",
        "desired_model": "models/gemini-3.1-flash-image-preview",
        "visual_style": "flat_vector",
        "title": "EV Fleet vs Diesel Vans",
        "subtitle": "Total cost, uptime, and footprint over five years",
        "footer_text": "Source: Logistics modernization program FY26",
        "exact_text_required": False,
        "text_preference": "summarize",
        "render_mode": "pure_image",
        "aspect_ratio": "4:5",
        "image_size": "1536x1920",
        "sections": [
            {
                "title": "Total Cost of Ownership",
                "icon_hint": "scale icon",
                "chart_hint": "three-column grid",
                "text_blocks": [
                    {"label": "EV Fleet", "body": "$410k / 5 yrs", "exact_text": False},
                    {"label": "Diesel Vans", "body": "$470k / 5 yrs", "exact_text": False},
                    {"label": "Savings", "body": "13% lower fuel + service", "exact_text": False},
                ],
            },
            {
                "title": "Reliability & Operations",
                "icon_hint": "clock badge",
                "text_blocks": [
                    {"label": "Uptime", "body": "EV: 96%  Diesel: 92%", "exact_text": False},
                    {"label": "Charging", "body": "45 min DC fast average", "exact_text": False},
                ],
            },
            {
                "title": "Sustainability",
                "icon_hint": "leaf icon",
                "chart_hint": "stacked bars",
                "text_blocks": [
                    {"label": "CO₂e Cut", "body": "−480 tons annually", "exact_text": False},
                    {"label": "Noise", "body": "EV routes 18% quieter", "exact_text": False},
                ],
            },
        ],
    },
    "concept_diagram": {
        "topic": "Edge AI safety envelope",
        "audience": "Tech team only",
        "desired_model": "models/gemini-3.1-flash-image-preview",
        "visual_style": "hand_drawn_line_art",
        "title": "Safety Envelope for Edge AI Robots",
        "subtitle": "How sensing, planning, and guardrails connect",
        "footer_text": "Draft for robotics guild review",
        "exact_text_required": False,
        "text_preference": "summarize",
        "render_mode": "hybrid_overlay",
        "aspect_ratio": "16:9",
        "image_size": "1920x1080",
        "sections": [
            {
                "title": "Perception",
                "icon_hint": "sensor halo",
                "text_blocks": [
                    {"label": "Inputs", "body": "LiDAR • vision • torque", "exact_text": False},
                    {"label": "Filtering", "body": "Kalman + anomaly flags", "exact_text": False},
                ],
            },
            {
                "title": "Policy Core",
                "icon_hint": "brain chip",
                "text_blocks": [
                    {"label": "Planner", "body": "Model predictive safety zone", "exact_text": False},
                    {"label": "Overrides", "body": "Hard-stop, slow-roll, fallback", "exact_text": False},
                ],
            },
            {
                "title": "Environment Envelope",
                "icon_hint": "shield ring",
                "text_blocks": [
                    {"label": "Zones", "body": "Green (safe), Amber (caution), Red (halt)", "exact_text": False},
                    {"label": "Broadcast", "body": "Edge → cloud telemetry digest", "exact_text": False},
                ],
            },
        ],
    },
    "educational_diagram": {
        "topic": "River delta nutrient cycle",
        "audience": "Big conference audience",
        "desired_model": "models/gemini-2.5-flash-image",
        "visual_style": "watercolor",
        "title": "How River Deltas Feed Coastal Reefs",
        "subtitle": "Nutrient and sediment journey explained",
        "footer_text": "Classroom handout, Spring 2026",
        "exact_text_required": False,
        "text_preference": "summarize",
        "render_mode": "pure_image",
        "aspect_ratio": "3:2",
        "image_size": "1800x1200",
        "sections": [
            {
                "title": "Upland Inputs",
                "icon_hint": "mountain with rain",
                "text_blocks": [
                    {"label": "Snowmelt", "body": "Carries nitrate minerals", "exact_text": False},
                    {"label": "Soil Runoff", "body": "Adds organic carbon", "exact_text": False},
                ],
            },
            {
                "title": "Delta Mixing Zone",
                "icon_hint": "braided channels",
                "text_blocks": [
                    {"label": "Wetlands", "body": "Store sediment, slow flow", "exact_text": False},
                    {"label": "Microbes", "body": "Convert nitrogen for plankton", "exact_text": False},
                ],
            },
            {
                "title": "Reef Delivery",
                "icon_hint": "coral icon",
                "text_blocks": [
                    {"label": "Upwelling", "body": "Pushes nutrients to polyps", "exact_text": False},
                    {"label": "Larval Drift", "body": "Seeds new coral heads", "exact_text": False},
                ],
            },
        ],
    },
    "explainer_graphic": {
        "topic": "Realtime fraud response stack",
        "audience": "Whole department tech & non tech",
        "desired_model": "models/gemini-3.1-flash-image-preview",
        "visual_style": "cyberpunk_neon",
        "title": "How We Stop Card Fraud in 90 Seconds",
        "subtitle": "Signal fusion → models → playbooks",
        "footer_text": "Prepared for Q2 trust council",
        "exact_text_required": False,
        "text_preference": "summarize",
        "render_mode": "pure_image",
        "aspect_ratio": "16:9",
        "image_size": "2560x1440",
        "sections": [
            {
                "title": "Signal Capture",
                "icon_hint": "antenna burst",
                "text_blocks": [
                    {"label": "Device DNA", "body": "Geo + jailbreak status", "exact_text": False},
                    {"label": "Merchant IQ", "body": "Behavioral fingerprint", "exact_text": False},
                ],
            },
            {
                "title": "Decision Brain",
                "icon_hint": "neon brain",
                "text_blocks": [
                    {"label": "Streaming model", "body": "Gemini 1M token window", "exact_text": False},
                    {"label": "Policy layer", "body": "Risk tiers auto-updated", "exact_text": False},
                ],
            },
            {
                "title": "Playbook Launch",
                "icon_hint": "rocket badge",
                "text_blocks": [
                    {"label": "Autoblock", "body": "Freeze + SMS confirm", "exact_text": False},
                    {"label": "Escalate", "body": "Route to trust-on-call", "exact_text": False},
                ],
            },
        ],
    },
    "line_art_infographic": {
        "topic": "API request lifecycle",
        "audience": "Tech team only",
        "desired_model": "models/gemini-2.5-flash-image",
        "visual_style": "hand_drawn_line_art",
        "title": "From Client Call to Durable Event",
        "subtitle": "Line-art walkthrough of our API stack",
        "footer_text": "Internal developer enablement",
        "exact_text_required": True,
        "text_preference": "exact",
        "render_mode": "hybrid_overlay",
        "aspect_ratio": "1:1",
        "image_size": "1536x1536",
        "sections": [
            {
                "title": "Request Edge",
                "icon_hint": "browser tab doodle",
                "text_blocks": [
                    {"label": "Auth", "body": "mTLS + scope check", "exact_text": True},
                    {"label": "Throttle", "body": "25 req/sec/client", "exact_text": True},
                ],
            },
            {
                "title": "Service Mesh",
                "icon_hint": "mesh nodes",
                "text_blocks": [
                    {"label": "Routing", "body": "Consistent hashing shards", "exact_text": True},
                    {"label": "Observability", "body": "Trace ID promoted", "exact_text": True},
                ],
            },
            {
                "title": "Event Lake",
                "icon_hint": "data bucket",
                "text_blocks": [
                    {"label": "Writer", "body": "Exactly-once Kafka sink", "exact_text": True},
                    {"label": "Replay", "body": "Sidecar rehydrates cache", "exact_text": True},
                ],
            },
        ],
    },
    "mind_map": {
        "topic": "GenAI governance pillars",
        "audience": "Whole department tech & non tech",
        "desired_model": "models/gemini-3.1-flash-image-preview",
        "visual_style": "childrens_book",
        "title": "Mind Map: Governing Generative AI",
        "subtitle": "Policy, tooling, and people threads",
        "footer_text": "Enterprise AI office August 2026",
        "exact_text_required": False,
        "text_preference": "summarize",
        "render_mode": "pure_image",
        "aspect_ratio": "2:1",
        "image_size": "2048x1024",
        "sections": [
            {
                "title": "Policy",
                "icon_hint": "scroll",
                "text_blocks": [
                    {"label": "Usage tiers", "body": "Public / internal / restricted", "exact_text": False},
                    {"label": "Model registry", "body": "Approved releases only", "exact_text": False},
                ],
            },
            {
                "title": "Tooling",
                "icon_hint": "gear cloud",
                "text_blocks": [
                    {"label": "Guardrails", "body": "Prompt filters + eval harness", "exact_text": False},
                    {"label": "Observability", "body": "Cost + latency budget", "exact_text": False},
                ],
            },
            {
                "title": "People",
                "icon_hint": "team avatars",
                "text_blocks": [
                    {"label": "AI Stewards", "body": "One per product line", "exact_text": False},
                    {"label": "Upskilling", "body": "Quarterly labs + office hours", "exact_text": False},
                ],
            },
        ],
    },
    "process_flow": {
        "topic": "Incident response playbook",
        "audience": "Stakeholder show-and-tell",
        "desired_model": "models/gemini-2.5-flash-image",
        "visual_style": "flat_vector",
        "title": "Major Incident Flow",
        "subtitle": "Detect → triage → resolve within 60 minutes",
        "footer_text": "SRE on-call reference",
        "exact_text_required": False,
        "text_preference": "summarize",
        "render_mode": "pure_image",
        "aspect_ratio": "16:9",
        "image_size": "1920x1080",
        "sections": [
            {
                "title": "Detect",
                "icon_hint": "radar",
                "text_blocks": [
                    {"label": "Signals", "body": "PagerDuty, anomaly bots", "exact_text": False},
                    {"label": "Auto-priority", "body": "P1 if customer impact", "exact_text": False},
                ],
            },
            {
                "title": "Stabilize",
                "icon_hint": "firewall",
                "text_blocks": [
                    {"label": "Responder swarm", "body": "Comms + fix lead", "exact_text": False},
                    {"label": "Customer note", "body": "Status page update <15 min", "exact_text": False},
                ],
            },
            {
                "title": "Resolve & Learn",
                "icon_hint": "checkmark badge",
                "text_blocks": [
                    {"label": "Rollback or patch", "body": "Change freeze engaged", "exact_text": False},
                    {"label": "Post-incident", "body": "Blameless review + action log", "exact_text": False},
                ],
            },
        ],
    },
    "roadmap": {
        "topic": "Data product roadmap",
        "audience": "Stakeholder show-and-tell",
        "desired_model": "models/gemini-3.1-flash-image-preview",
        "visual_style": "cartoon_3d",
        "title": "Customer Data Platform Roadmap",
        "subtitle": "Four-quarter plan toward self-serve analytics",
        "footer_text": "Draft v1 for steering committee",
        "exact_text_required": False,
        "text_preference": "summarize",
        "render_mode": "pure_image",
        "aspect_ratio": "3:2",
        "image_size": "2700x1800",
        "sections": [
            {
                "title": "Q1 – Foundation",
                "icon_hint": "pillar",
                "text_blocks": [
                    {"label": "Unified schema", "body": "Consent + profile stitched", "exact_text": False},
                    {"label": "Event bus", "body": "Streaming ingestion GA", "exact_text": False},
                ],
            },
            {
                "title": "Q2 – Activation",
                "icon_hint": "rocket",
                "text_blocks": [
                    {"label": "Audience builder", "body": "Beta with growth team", "exact_text": False},
                    {"label": "API kits", "body": "Partner sandbox ready", "exact_text": False},
                ],
            },
            {
                "title": "Q3/Q4 – Scale",
                "icon_hint": "trophy",
                "text_blocks": [
                    {"label": "AI insights", "body": "Predictive churn cards", "exact_text": False},
                    {"label": "Global roll-out", "body": "Multi-region clusters", "exact_text": False},
                ],
            },
        ],
    },
    "scientific_illustration": {
        "topic": "Carbon capture and storage",
        "audience": "Big conference audience",
        "desired_model": "models/gemini-3.1-flash-image-preview",
        "visual_style": "oil_painting",
        "title": "Inside a Carbon Capture Plant",
        "subtitle": "From flue gas to mineralized storage",
        "footer_text": "Energy Futures Summit poster",
        "exact_text_required": False,
        "text_preference": "summarize",
        "render_mode": "pure_image",
        "aspect_ratio": "4:5",
        "image_size": "2048x2560",
        "sections": [
            {
                "title": "Absorption Towers",
                "icon_hint": "tower cutaway",
                "text_blocks": [
                    {"label": "Solvent spray", "body": "Amines bind CO₂ molecules", "exact_text": False},
                    {"label": "Heat exchange", "body": "Recovers energy for reuse", "exact_text": False},
                ],
            },
            {
                "title": "Compression & Transport",
                "icon_hint": "pipes",
                "text_blocks": [
                    {"label": "Supercritical state", "body": "Pipelines to injection site", "exact_text": False},
                    {"label": "Leak guardians", "body": "Fiber optical sensing grid", "exact_text": False},
                ],
            },
            {
                "title": "Geologic Storage",
                "icon_hint": "earth layers",
                "text_blocks": [
                    {"label": "Basalt wells", "body": "CO₂ mineralizes in 24 months", "exact_text": False},
                    {"label": "Monitoring", "body": "Seismic + satellite checks", "exact_text": False},
                ],
            },
        ],
    },
    "statistical_infographic": {
        "topic": "Customer retention signals",
        "audience": "Stakeholder show-and-tell",
        "desired_model": "models/gemini-2.5-flash-image",
        "visual_style": "comic_book",
        "title": "Retention Dashboard at a Glance",
        "subtitle": "Q1 cohort analytics",
        "footer_text": "Marketing ops weekly readout",
        "exact_text_required": False,
        "text_preference": "summarize",
        "render_mode": "pure_image",
        "aspect_ratio": "1:1",
        "image_size": "2048x2048",
        "sections": [
            {
                "title": "Headline Metrics",
                "icon_hint": "big counter",
                "text_blocks": [
                    {"label": "Net Retention", "body": "108% (+3 pt)", "exact_text": False},
                    {"label": "Churn", "body": "2.7% (target 3%)", "exact_text": False},
                ],
            },
            {
                "title": "Top Drivers",
                "icon_hint": "bar chart",
                "text_blocks": [
                    {"label": "Adoption", "body": "+11% weekly active workspaces", "exact_text": False},
                    {"label": "NPS Detractors", "body": "Down 6% after new onboarding", "exact_text": False},
                ],
            },
            {
                "title": "Action Board",
                "icon_hint": "sticky notes",
                "text_blocks": [
                    {"label": "Premium nudges", "body": "Target EDU + Tier 2", "exact_text": False},
                    {"label": "Health alerts", "body": "Focus on accounts <80 health", "exact_text": False},
                ],
            },
        ],
    },
    "vertical_timeline": {
        "topic": "Retail media program launch",
        "audience": "Big conference audience",
        "desired_model": "models/gemini-3.1-flash-image-preview",
        "visual_style": "pixel_art_16bit",
        "title": "Retail Media Milestones",
        "subtitle": "From pilot to nationwide rollout",
        "footer_text": "Updated: Mar 2026",
        "exact_text_required": True,
        "text_preference": "exact",
        "render_mode": "hybrid_overlay",
        "aspect_ratio": "9:16",
        "image_size": "1080x1920",
        "sections": [
            {
                "title": "Q2 2026",
                "icon_hint": "pixel calendar",
                "text_blocks": [
                    {"label": "Pilot", "body": "5 flagship stores live", "exact_text": True},
                    {"label": "Metrics", "body": "CTR 3.2% vs 2.4% goal", "exact_text": True},
                ],
            },
            {
                "title": "Q3 2026",
                "icon_hint": "pixel truck",
                "text_blocks": [
                    {"label": "Expansion", "body": "Regional clusters x3", "exact_text": True},
                    {"label": "Partners", "body": "Add 12 CPG co-ops", "exact_text": True},
                ],
            },
            {
                "title": "Q4 2026",
                "icon_hint": "pixel trophy",
                "text_blocks": [
                    {"label": "Nationwide", "body": "All 480 stores onboard", "exact_text": True},
                    {"label": "Next", "body": "Shoppable TV pilot", "exact_text": True},
                ],
            },
        ],
    },
    "whiteboard_explainer": {
        "topic": "ML training pipeline",
        "audience": "Tech team only",
        "desired_model": "models/gemini-2.5-flash-image",
        "visual_style": "claymation",
        "title": "Whiteboard: Model Training Factory",
        "subtitle": "Data → features → training → eval",
        "footer_text": "Studio Chat preset demo",
        "exact_text_required": False,
        "text_preference": "summarize",
        "render_mode": "pure_image",
        "aspect_ratio": "16:9",
        "image_size": "1920x1080",
        "sections": [
            {
                "title": "Data Sourcing",
                "icon_hint": "whiteboard bucket",
                "text_blocks": [
                    {"label": "Pipelines", "body": "CDC → bronze lake", "exact_text": False},
                    {"label": "Quality", "body": "Great Expectations gates", "exact_text": False},
                ],
            },
            {
                "title": "Feature Studio",
                "icon_hint": "marker gear",
                "text_blocks": [
                    {"label": "Feature views", "body": "14 day sliding window", "exact_text": False},
                    {"label": "Catalog", "body": "Version + owners noted", "exact_text": False},
                ],
            },
            {
                "title": "Training & Eval",
                "icon_hint": "whiteboard rocket",
                "text_blocks": [
                    {"label": "Auto trainers", "body": "GPU farm spin-up", "exact_text": False},
                    {"label": "Guardrails", "body": "Bias + drift dashboards", "exact_text": False},
                ],
            },
        ],
    },
}

