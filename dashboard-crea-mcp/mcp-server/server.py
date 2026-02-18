import uvicorn
from mcp.server.fastmcp import FastMCP
import yaml
import os
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, text
from litellm import completion
from typing import Any, Dict, List

# Load configuration
CONFIG_PATH = os.getenv("MCP_CONFIG_PATH", "../shared/config.yaml")

def load_config() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file not found at {CONFIG_PATH}, using defaults.")
        return {"tools": {}}

config = load_config()

# Initialize FastMCP Server
mcp = FastMCP("Dashboard-Configurable-MCP")

@mcp.tool()
def get_server_status() -> str:
    """Returns the current status and configuration of the MCP server."""
    return f"Server is running. Active tools: {list(config.get('tools', {}).keys())}"

# 1. LLM Tool
llm_config = config.get("tools", {}).get("llm", {})
if llm_config.get("enabled", False):
    @mcp.tool()
    def chat_with_llm(prompt: str) -> str:
        """Chat with the configured LLM."""
        try:
            model = llm_config.get("model", "gpt-3.5-turbo")
            api_key = llm_config.get("api_key")
            response = completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                api_key=api_key
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error querying LLM: {str(e)}"

# 2. Scraper Tool
scraper_config = config.get("tools", {}).get("scraper", {})
if scraper_config.get("enabled", False):
    @mcp.tool()
    def scrape_website(url: str) -> str:
        """Scrape content from a URL."""
        try:
            headers = {"User-Agent": scraper_config.get("user_agent", "MCPScraper/1.0")}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            # remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            # break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text[:10000] # Return first 10k chars
        except Exception as e:
            return f"Error scraping URL: {str(e)}"

# 3. Database Tool
db_config = config.get("tools", {}).get("database", {})
if db_config.get("enabled", False):
    connections = {conn["name"]: conn["uri"] for conn in db_config.get("connections", [])}
    
    @mcp.tool()
    def query_database(query: str, connection_name: str = "default") -> str:
        """Run a SQL query on the configured database."""
        if connection_name not in connections:
             return f"Error: Connection '{connection_name}' not found in configuration."
        
        uri = connections[connection_name]
        try:
            engine = create_engine(uri)
            with engine.connect() as conn:
                result = conn.execute(text(query))
                keys = result.keys()
                rows = [dict(zip(keys, row)) for row in result.fetchall()]
                return str(rows)
        except Exception as e:
            return f"Error executing query: {str(e)}"

if __name__ == "__main__":
    # Start the server using uvicorn when running directly
    print("Starting MCP Server...")
    # mcp.run() handles everything including uvicorn under the hood for sse
    # We must bind to 0.0.0.0 to be accessible from outside the container
    import uvicorn
    # Create the Starlette app from the MCP server
    app = mcp.sse_app
    uvicorn.run(app, host="0.0.0.0", port=8000)
