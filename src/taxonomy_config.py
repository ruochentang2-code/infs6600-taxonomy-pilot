"""Built-in seven-category taxonomy supplied for the CS-44 project."""

from __future__ import annotations

import copy
import json
from pathlib import Path


DEFAULT_TAXONOMY = {
    "version": "2026-09-01-cs44-scope",
    "counting_unit": (
        "One distinct outline item (overview paragraph, learning outcome, assessment "
        "row, or weekly-schedule row) classified into a category."
    ),
    "categories": [
        {
            "id": "work_integrated_applied",
            "name": "Work-Integrated and Applied Learning",
            "definition": (
                "An educational approach that explicitly merges theory with real-world "
                "practice and embeds authentic industry, workplace or community-relevant "
                "work and tasks into a unit of study."
            ),
            "threshold": 3.0,
            "rules": [
                {
                    "label": "industry or business partner",
                    "pattern": (
                        "industry partner|business partner|partner briefing|pitch to partner|"
                        "partner's business|partner business"
                    ),
                    "weight": 4.0,
                },
                {
                    "label": "actual organisation or professional context",
                    "pattern": (
                        "actual business organisation|actual business problem|"
                        "actual business professionals"
                    ),
                    "weight": 4.0,
                },
                {
                    "label": "authentic practice",
                    "pattern": (
                        "authentic situations|authentic problem|authentic industry|"
                        "workplace project|industry project|consulting project|"
                        "work-integrated learning"
                    ),
                    "weight": 3.5,
                },
                {
                    "label": "professional presentation",
                    "pattern": "boardroom presentation|project presentation",
                    "weight": 3.5,
                },
                {
                    "label": "theory-practice integration",
                    "pattern": "theory and practice|theory with real-world practice",
                    "weight": 2.5,
                },
                {
                    "label": "practical teamwork",
                    "pattern": "practical teamwork experience",
                    "weight": 2.0,
                },
                {
                    "label": "career readiness",
                    "pattern": "career-readiness|career readiness|professional skills",
                    "weight": 1.5,
                },
                {
                    "label": "project immersion",
                    "pattern": "project immersion",
                    "weight": 2.0,
                },
            ],
        },
        {
            "id": "project_problem_based",
            "name": "Project- and Problem-Based Learning",
            "definition": (
                "Learning organised around real-world problems or challenges using "
                "problem-solving, decision-making and investigative skills."
            ),
            "threshold": 3.0,
            "rules": [
                {"label": "explicit project/problem method", "pattern": "project-based learning|problem-based learning|pbl", "weight": 4.0},
                {"label": "challenge method", "pattern": "challenge-based learning|complex challenge|interdisciplinary project", "weight": 3.5},
                {"label": "design thinking", "pattern": "design thinking", "weight": 3.5},
                {"label": "real-world problem", "pattern": "real-world problem|real-life business problem|actual business problem", "weight": 3.5},
                {"label": "substantial project", "pattern": "group project|individual project|project report|capstone project", "weight": 3.0},
            ],
        },
        {
            "id": "community_learning",
            "name": "Community Learning",
            "definition": "Learning undertaken with and for communities and communities of practice.",
            "threshold": 3.0,
            "rules": [
                {"label": "service/community learning", "pattern": "service-learning|service learning|community-engaged learning|community learning", "weight": 4.0},
                {"label": "community project", "pattern": "community project|civic engagement project|social impact project", "weight": 3.5},
                {"label": "field/professional community", "pattern": "field study|field studies|professional communities of practice|community of practice", "weight": 3.5},
            ],
        },
        {
            "id": "entrepreneurial_learning",
            "name": "Entrepreneurial Learning",
            "definition": "Learning that develops opportunity recognition and turns creative ideas into new ventures or action.",
            "threshold": 3.0,
            "rules": [
                {"label": "venture/start-up", "pattern": "start-up|startup|new venture|entrepreneurial", "weight": 4.0},
                {"label": "product development", "pattern": "product development project|new product development", "weight": 3.5},
                {"label": "opportunity recognition", "pattern": "recognise opportunities|recognize opportunities|opportunity recognition", "weight": 3.5},
                {"label": "business pitch", "pattern": "business pitch|pitch competition|pitch to", "weight": 3.0},
            ],
        },
        {
            "id": "technology_mediated",
            "name": "Technology-Mediated Learning",
            "definition": "Learning in which digital tools mediate access to materials, teachers, peers or experiential activities.",
            "threshold": 3.0,
            "rules": [
                {"label": "immersive technology", "pattern": "virtual reality|augmented reality|vr/ar|digital twin|immersive scenario", "weight": 4.0},
                {"label": "AI-mediated learning", "pattern": "ai-mediated|ai mediated|generative ai activity", "weight": 4.0},
                {"label": "game-based learning", "pattern": "gamification|serious game|educational game", "weight": 4.0},
                {"label": "virtual simulation", "pattern": "virtual simulation|online simulation", "weight": 3.5},
                {"label": "technology-mediated", "pattern": "technology-mediated learning|technology mediated learning", "weight": 4.0},
            ],
        },
        {
            "id": "hybrid_learning",
            "name": "Hybrid Learning",
            "definition": "Learning that intentionally combines face-to-face teaching with online digital instruction.",
            "threshold": 3.0,
            "rules": [
                {"label": "explicit hybrid model", "pattern": "hybrid learning|hyflex|blended learning", "weight": 4.0},
                {"label": "flipped classroom", "pattern": "flipped classroom|flipped learning", "weight": 4.0},
                {"label": "self-paced online modules", "pattern": "self-paced module|self paced module|online module", "weight": 3.5},
            ],
        },
        {
            "id": "simulation_case_based",
            "name": "Simulation and Case-Based Learning",
            "definition": (
                "Learning through real-world scenarios, cases or simulations that allow "
                "students to apply knowledge and skills in contexts resembling professional "
                "practice."
            ),
            "threshold": 3.0,
            "rules": [
                {
                    "label": "explicit simulation",
                    "pattern": (
                        "business simulation|lab-based simulation|virtual simulation|"
                        "simulation-based|simulation"
                    ),
                    "weight": 4.0,
                },
                {
                    "label": "explicit case method",
                    "pattern": "case study analysis|case studies|case study|case competition",
                    "weight": 4.0,
                },
                {
                    "label": "explicit role play",
                    "pattern": "role-play|role play",
                    "weight": 4.0,
                },
                {
                    "label": "explicit scenario method",
                    "pattern": (
                        "scenario-based learning|open-ended business scenarios|"
                        "business scenarios|real-world scenarios"
                    ),
                    "weight": 3.5,
                },
            ],
        },
    ],
}


def load_taxonomy(path: Path | None = None) -> dict:
    """Load a caller-supplied taxonomy, or return a safe copy of the pilot default."""
    if path is not None:
        return json.loads(path.read_text(encoding="utf-8"))
    return copy.deepcopy(DEFAULT_TAXONOMY)
