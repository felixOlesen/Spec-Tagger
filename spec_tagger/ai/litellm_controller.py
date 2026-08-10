import litellm
from dotenv import load_dotenv


class LiteLLMController:
    def __init__(self, provider: str, model_name: str) -> None:
        load_dotenv()
        self.provider = provider
        self.model_name = model_name
        self.provider_route = self.get_provider_route(provider)

    def get_provider_route(self, provdier_name) -> str:
        match provdier_name:
            case "gemini":
                self.provider_route = f"gemini/{self.model_name}"

    def send_prompt(self):
        try:
            response = litellm.completion(
                model=self.provider_route,
                messages=[
                    {
                        "role": "user",
                        "content": "write a small poem for me with 50 dashes at the beginning and at the end",
                    }
                ],
            )
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
