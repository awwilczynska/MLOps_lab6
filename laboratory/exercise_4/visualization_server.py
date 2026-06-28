import base64
import io
from typing import Annotated

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fastmcp import FastMCP

mcp = FastMCP("Visualization")


@mcp.tool(description="Create a line plot from one or more data series and return it as a base64-encoded PNG image.")
def line_plot(
    data: Annotated[list[list[float]], "One or more lists of numbers, each plotted as a separate line."],
    title: Annotated[str, "Plot title."] = "",
    x_label: Annotated[str, "Label for the x-axis."] = "",
    y_label: Annotated[str, "Label for the y-axis."] = "",
    legend: Annotated[bool, "Whether to show a legend."] = False,
) -> str:
    fig, ax = plt.subplots()

    for i, series in enumerate(data):
        ax.plot(series, label=f"Series {i + 1}")

    if title:
        ax.set_title(title)
    if x_label:
        ax.set_xlabel(x_label)
    if y_label:
        ax.set_ylabel(y_label)
    if legend:
        ax.legend()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


if __name__ == "__main__":
    # TEST: call the tool directly, decode and save the image
    encoded = line_plot(
        data=[[1, 4, 9, 16, 25], [2, 3, 5, 7, 11]],
        title="Sample plot",
        x_label="Index",
        y_label="Value",
        legend=True,
    )
    with open("test_plot.png", "wb") as f:
        f.write(base64.b64decode(encoded))
    print("Test image saved to test_plot.png")

    mcp.run(transport="streamable-http", port=8003)
