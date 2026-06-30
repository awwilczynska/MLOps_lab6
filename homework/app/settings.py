from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    tavily_api_key: str
    tavily_mcp_base_url: str = "https://mcp.tavily.com/mcp/?tavilyApiKey="

    # NOTE: vLLM is not used here because it cannot run efficiently on a
    # CPU-only Mac (no CUDA, extremely slow inference even for small models).
    # The Google Gemini API exposes an OpenAI-compatible endpoint, so the
    # same OpenAI Python client and tool-calling flow works without change.
    gemini_api_key: str
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_model: str = "gemini-2.5-flash"

    openweather_mcp_host: str = "localhost"
    openweather_mcp_port: int = 8001

    tool_loop_limit: int = 10
    max_completion_tokens: int = 1024

    @computed_field
    @property
    def mcp_servers(self) -> dict[str, str]:
        return {
            "tavily": f"{self.tavily_mcp_base_url}{self.tavily_api_key}",
            "openweather": (
                f"http://{self.openweather_mcp_host}:{self.openweather_mcp_port}/mcp"
            ),
        }


_settings = AppSettings()  # type: ignore


def get_settings() -> AppSettings:
    return _settings
