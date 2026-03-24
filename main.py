import random
from fastmcp import FastMCP

# create a fastMCP server instance
mcp=FastMCP(name="demo project")

@mcp.tool
def roll_dice(n_dice:int=1) -> list[int]:
    """Role n_dice 6-sided and return the result."""
    return [random.randint(1, 6) for _ in range(n_dice)]

@mcp.tool
def add_numbers(a:int, b:int) -> int:
    """Ad two numbers together"""
    return a+b

if __name__ == "__main__":
    # mcp.run() # don't add any args if you want local server
    mcp.run(transport="streamable-http",
            host="0.0.0.0", # Required for remote access on most hosting platforms
            port=8000)