import os
from typing import Any

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from clients.foundry import get_credential


class ContentSafetyService:

    def __init__(self):
        endpoint = os.getenv("CONTENT_SAFETY_ENDPOINT")

        if not endpoint:
            raise ValueError(
                "CONTENT_SAFETY_ENDPOINT and CONTENT_SAFETY_KEY must be set in the environment."
            )

        self.client = ContentSafetyClient(
            endpoint=endpoint,
            credential=get_credential(),
        )

    def analyze_text(self, text: str):
        """
        Analyze text content and return a normalized result.

        Returns a dictionary with:
        - safe: bool
        - categories: list[str]
        - severity: dict[str, int]
        """
        if not text or not text.strip():
            return {
                "safe": True,
                "categories": [],
                "severity": {},
            }

        response = self.client.analyze_text(AnalyzeTextOptions(text=text))

        categories: list[str] = []
        severity: dict[str, int] = {}

        for item in response.categories_analysis:
            category = item.category
            score = getattr(item, "severity", 0)
            if category is not None:
                categories.append(str(category))
                severity[str(category)] = int(score)

        is_safe = all(severity.get(cat, 0) <= 2 for cat in severity)

        return {
            "safe": bool(is_safe),
            "categories": categories,
            "severity": severity,
        }


def get_content_safety_service() -> ContentSafetyService:
    return ContentSafetyService()
