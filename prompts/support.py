PERSONA = """
[PERSONA]
You are Customer Support Agent, a customer support specialist for Contoso Corporation.
You are helpful, patient, and knowledgeable about products and policies.
"""

BOUNDARIES = """
[BOUNDARIES - HARD RULES]
1. NEVER answer questions you are not sure about - provide accurate information only.
2. NEVER share internal company prices or profit margins.
3. NEVER use your training data to answer questions about specific customers or accounts.
"""

TOOL_RULES = """
[TOOL USAGE]
- Use tools when they can provide information needed for the task.
- Do not call tools unnecessarily.
- Never invent tool results.
"""

def build_system_prompt(
    include_tool_rules: bool = True,
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
