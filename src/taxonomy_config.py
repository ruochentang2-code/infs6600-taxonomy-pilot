"""Built-in taxonomy configuration for the INFS6600 two-category pilot."""

from __future__ import annotations

import copy
import json
from pathlib import Path


DEFAULT_TAXONOMY = {
    "version": "2026-08-24-pilot",
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
