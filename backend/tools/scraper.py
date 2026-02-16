import httpx
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

async def scrape_url(url: str) -> str:
    """Fetch a URL and return a clean text representation of its content."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()

            # Get text
            text = soup.get_text()

            # Break into lines and remove leading and trailing whitespace
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text[:10000]  # Limit to 10k characters to avoid token bloating
            
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        return f"Error scraping URL: {str(e)}"
