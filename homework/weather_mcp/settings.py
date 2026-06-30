from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openweather_api_key: str
    openweather_mcp_port: int = 8001


_settings = MCPSettings()  # type: ignore


def get_settings() -> MCPSettings:
    return _settings
