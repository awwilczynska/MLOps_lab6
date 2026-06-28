from typing import Annotated

from fastmcp import FastMCP

mcp = FastMCP("Weather forecast")


@mcp.tool(description="Get weather forecast at given country, city, and date")
def get_weather_forecast(
        country: Annotated[str, "The country the city is in."],
        city: Annotated[str, "The city to get the weather for."],
        date: Annotated[
            str,
            "The date to get the weather for, "
            'in the format "Year-Month-Day" (YYYY-MM-DD). '
            "At most 4 weeks into the future.",
        ],
) -> str:
    if country.lower() in {"united kingdom", "uk", "england"}:
        return "Fog and rain"
    else:
        return "Sunshine"


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8001)
