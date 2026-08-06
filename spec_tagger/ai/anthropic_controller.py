import anthropic
import logging


class AnthropicController:
    def __init__(self, api_key: str | None):
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
        self.available = self.client is not None
        if not self.available:
            logging.warning("ANTHROPIC API KEY not set. AI analysis has been skipped.")

        def _call(self, schema, system, user):
            if not self.available:
                return None
            try:
                resp = self.client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1500,
                    system=[
                        {
                            "type": "text",
                            "text": system,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    tools=[
                        {
                            "name": "record",
                            "description": "Record the verdict.",
                            "input_schema": schema.model_json_schema(),
                        }
                    ],
                    tool_choice={"type": "tool", "name": "record"},
                    messages=[{"role": "user", "content": user}],
                )
                block = next(b for b in resp.content if b.type == "tool_use")
                return schema(**block.input)
            except Exception as exception:
                logging.warning(
                    "AI analysis failed (%s) continuing without it.", exception
                )
                return None
