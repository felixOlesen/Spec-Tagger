import litellm
from litellm.exceptions import (
    AuthenticationError,
    RateLimitError,
    BadRequestError,
    APIConnectionError,
    ServiceUnavailableError,
)
from dotenv import load_dotenv
import json


class LiteLLMController:
    def __init__(self, provider: str, model_name: str, rate_limit: int) -> None:
        load_dotenv()
        self.provider = provider
        self.model_name = model_name
        self.provider_route = self.get_provider_route(provider)
        self.rate_limit = rate_limit
        self.token_usage_total = 0

    def get_provider_route(self, provdier_name) -> str:
        new_route = ""
        match provdier_name:
            case "gemini":
                new_route = f"gemini/{self.model_name}"
            case "nvidia_nim":
                new_route = f"nvidia_nim/{self.model_name}"
            case "openrouter":
                new_route = f"openrouter/{self.model_name}"
            case _:
                new_route = f"{self.provider}/{self.model_name}"

        return new_route

    def send_prompt(self, schema, user, system):
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
                num_retries=self.rate_limit,
            )
            if response:
                args = json.loads(
                    response.choices[0].message.tool_calls[0].function.arguments
                )
                usage_info = response.usage
                self.token_usage_total += usage_info.total_tokens

                try:
                    cost_usd = litellm.completion_cost(completion_response=response)
                except Exception:
                    print("Warning, no cost data could be found for the request")
                    cost_usd = None
                return schema(**args), usage_info, cost_usd
            else:
                raise ValueError("Response from LLM found to be None when received.")
        except AuthenticationError as e:
            print(f"Bad API key: {e}")
        except RateLimitError as e:
            print(f"Rate limited: {e}")
        except APIConnectionError as e:
            print(f"API Connection Error error: {e}")
        except BadRequestError as e:
            print(f"Bad Request Error error: {e}")
        except ServiceUnavailableError as e:
            print(f"Service Unavailable Error error: {e}")

    def parse_response(self, response, usage_info, cost_usd):
        print(f"LLM Response: \n{response}\n")
        print(f"Prompt Tokens: {usage_info.prompt_tokens}\n")
        print(f"Completion Tokens: {usage_info.completion_tokens}\n")
        print(f"Total Tokens: {usage_info.total_tokens}\n")
        print(f"Cost USD: {cost_usd}")

    def show_total_session_token_usage(self):
        print(f"Total Token Usage in Session: {self.token_usage_total}")

    def set_model_provider_and_name(self, provider: str, model_name: str):
        self.provider = provider
        self.model_name = model_name
