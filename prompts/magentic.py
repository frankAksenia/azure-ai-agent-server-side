"""Domain-independent prompts for Magentic progress evaluation and final output."""

PROGRESS_LEDGER_PROMPT = """
Evaluate the current conversation turn:
{task}

Available specialists and their capabilities:
{team}

Use these capabilities to select the specialist that can perform the next
needed action. Delegate record lookups and actions to their owner. Verify a
limitation with that specialist before declaring information unavailable;
previous assistant assumptions are not evidence of unavailable capabilities.

Set is_request_satisfied.answer to true when a supported response is ready:
- The current request is answered using verified findings.
- A necessary clarification question is ready and further work needs user input.
- The specialist has completed its part and an application-controlled step,
  such as user confirmation, must happen next.
- A verified limitation and an actionable next step are ready, and no available
  specialist can advance the request with the current information.
Otherwise set it to false and delegate an action that can be performed now.
A greeting can be answered directly without specialist delegation.

Completing a turn does not mean the underlying issue is resolved. No new user
input arrives during this workflow: return the prepared question or next step
instead of waiting, repeating it, or delegating work conditional on a future
reply. Use prior conversation only to interpret the current request.

Assess whether actions are repeating and whether recent messages add useful
information. If complete, next_speaker must still name a valid participant,
but it will not run; instruction_or_question should describe the final response.

Return only JSON with the five fields below and a reason for each answer.
The first three answers must be booleans; next_speaker.answer must be one of
{names}; instruction_or_question.answer must be a string.

{{
  "is_request_satisfied": {{"reason": "...", "answer": false}},
  "is_in_loop": {{"reason": "...", "answer": false}},
  "is_progress_being_made": {{"reason": "...", "answer": true}},
  "next_speaker": {{"reason": "...", "answer": "participant name"}},
  "instruction_or_question": {{"reason": "...", "answer": "..."}}
}}
"""

FINAL_ANSWER_PROMPT = """
Respond to the user's current request:
{task}

Use verified specialist findings from the conversation. If user input is needed,
ask one concise clarification question. If an application-controlled step is
pending, explain that next step without claiming the action has been completed.
Otherwise give the supported answer or a verified limitation with a next step.
Current findings take precedence over earlier unsupported assumptions.

Keep the response concise. Do not claim the underlying issue is resolved merely
because this turn is complete. Do not include internal planning, routing, or
progress-ledger JSON.
"""
