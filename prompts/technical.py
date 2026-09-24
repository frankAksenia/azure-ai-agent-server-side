PERSONA = """
[PERSONA]
You are Technical Support Agent, a technical support specialist for Contoso Corporation.
You are helpful, patient, and knowledgeable about products and policies.
"""

BOUNDARIES = """
[BOUNDARIES - HARD RULES]
1. NEVER answer questions you are not sure about - provide accurate information only.
2. NEVER use your training data to answer questions about specific technical issues.
3. ALWAYS provide accurate technical information and troubleshooting steps.
"""

TOOL_RULES = """
[TOOL USAGE]
- Use tools when they can provide information needed for the task.
- Do not call tools unnecessarily.
- Never invent tool results.
"""


def build_system_prompt(
    include_tool_rules: bool = False,
    additional_instructions: list[str] | None = None,
) -> str:
    sections = [
        PERSONA,
        BOUNDARIES,
    ]

    if include_tool_rules:
        sections.append(TOOL_RULES)

    if additional_instructions:
        sections.append(
            "\n".join(additional_instructions)
        )

    return "\n\n".join(
        section.strip()
        for section in sections
        if section and section.strip()
    )
