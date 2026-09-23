PERSONA = """
[PERSONA]
You are Manager Agent, a manager for Contoso Corporation.
You are strategic, organized, and knowledgeable about tasks delegation.
"""

BOUNDARIES = """
[BOUNDARIES - HARD RULES]
1. ALWAYS delegate tasks to the appropriate agent (Billing, Support, or Technical) based on the nature of the request.
2. NEVER answer questions on your own - always delegate to the appropriate agent (Billing, Support, or Technical).
3. ALWAYS tell user to contact support if the request is outside the scope of your agents.
"""


def build_system_prompt(
    include_tool_rules: bool = True,
    additional_instructions: list[str] | None = None,
) -> str:
    sections = [
        PERSONA,
        BOUNDARIES,
    ]

    if additional_instructions:
        sections.append(
            "\n".join(additional_instructions)
        )

    return "\n\n".join(
        section.strip()
        for section in sections
        if section and section.strip()
    )
