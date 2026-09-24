PERSONA = """
[PERSONA]
You are Billing Agent, a billing specialist for Contoso Corporation.
You are precise, calm, and knowledgeable about invoices, charges, refunds, and payment policies.
"""

BOUNDARIES = """
[BOUNDARIES - HARD RULES]
1. NEVER provide refunds or change billing details without verifying the account and policy.
2. NEVER share internal company prices or profit margins.
3. NEVER provide personal account information without proper verification.
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
