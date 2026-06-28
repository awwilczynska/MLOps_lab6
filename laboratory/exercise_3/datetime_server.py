import datetime

from fastmcp import FastMCP

mcp = FastMCP("Date and time")


@mcp.tool(description='Returns current date in the format "Year-Month-Day" (YYYY-MM-DD)')
def get_current_date() -> str:
    return datetime.date.today().isoformat()


@mcp.tool(
    description='Returns current date and time in ISO 8601 format up to seconds (YYYY-MM-DDTHH:MM:SS)'
)
def get_current_datetime() -> str:
    return datetime.datetime.now().replace(microsecond=0).isoformat()


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8002)
