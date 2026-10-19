from azure.ai.contentsafety.models import AnalyzeTextOptions
from clients.content_safety_client import create_content_safety_client


class ContentSafetyService:

    def __init__(self, credential):
        self._client = create_content_safety_client(credential)

    def close(self):
        self._client.close()

    def analyze_text(self, text: str):
        if not text or not text.strip():
            return {
                "safe": True,
                "categories": [],
                "severity": {},
            }

        response = self._client.analyze_text(AnalyzeTextOptions(text=text))

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


def get_content_safety_service(credential) -> ContentSafetyService:
    return ContentSafetyService(credential)
