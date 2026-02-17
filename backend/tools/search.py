from duckduckgo_search import DDGS
import logging

logger = logging.getLogger(__name__)

async def search_web(query: str, max_results: int = 5) -> str:
    """Perform a web search using DuckDuckGo and return summarized results."""
    try:
        logger.info(f"🔎 Buscando en web: {query}")
        results = DDGS().text(query, max_results=max_results)
        
        if not results:
            return "No se encontraron resultados en la web."

        formatted_results = []
        for r in results:
            title = r.get('title', 'Sin título')
            link = r.get('href', '#')
            body = r.get('body', '')
            formatted_results.append(f"**{title}**\n{body}\n[Enlace]({link})")

        return "\n\n".join(formatted_results)
            
    except Exception as e:
        logger.error(f"Error searching web for '{query}': {str(e)}")
        return f"Error al buscar en la web: {str(e)}"
