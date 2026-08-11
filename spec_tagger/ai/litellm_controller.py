import litellm
from dotenv import load_dotenv
import json


class LiteLLMController:
    def __init__(self, provider: str, model_name: str) -> None:
        load_dotenv()
        self.provider = provider
        self.model_name = model_name
        self.provider_route = self.get_provider_route(provider)

    def get_provider_route(self, provdier_name) -> str:
        new_route = ""
        match provdier_name:
            case "gemini":
                new_route = f"gemini/{self.model_name}"

        return new_route

    def send_prompt(self):
        try:
            response = litellm.completion(
                model=self.provider_route,  # "anthropic/claude-sonnet-4-6", "gpt-4o", ...
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "record",
                            "parameters": schema.model_json_schema(),
                        },
                    }
                ],
                tool_choice={"type": "function", "function": {"name": "record"}},
            )
            response = litellm.completion(
                model=self.provider_route,
                messages=[
                    {
                        "role": "user",
                        "content": "write a small poem for me with 50 dashes at the beginning and at the end",
                    }
                ],
            )
            args = json.loads(resp.choices[0].message.tool_calls[0].function.arguments)
            return schema(**args)
            self.parse_response(response)
        except litellm.AuthenticationError as e:
            print(f"Bad API key: {e}")
        except litellm.RateLimitError as e:
            print(f"Rate limited: {e}")
        except litellm.APIError as e:
            print(f"API error: {e}")

    def parse_response(self, response):
        print(response["message"])

    def load_prompt_template(self):
        pass

    def set_model_provider_and_name(self, provider: str, model_name: str):
        self.provider = provider
        self.model_name = model_name


load_dotenv()
