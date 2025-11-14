"""
Tools for web tasks.
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from .base import BaseTool, ToolCategory, ToolOutput


class WebScraperTool(BaseTool):
    """Scrape content from a web page."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB

    @property
    def requires_approval(self) -> bool:
        return False  # Read-only operation

    def execute(
        self,
        url: str,
        selector: Optional[str] = None,
        extract_links: bool = False
    ) -> ToolOutput:
        """
        Scrape content from a web page.

        Args:
            url: URL to scrape
            selector: Optional CSS selector to extract specific content
            extract_links: Whether to extract all links

        Returns:
            ToolOutput with scraped content
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            result = {
                "url": url,
                "status_code": response.status_code,
                "title": soup.title.string if soup.title else None
            }

            if selector:
                elements = soup.select(selector)
                result["selected_content"] = [elem.get_text(strip=True) for elem in elements]
            else:
                result["text"] = soup.get_text(strip=True)

            if extract_links:
                links = []
                for link in soup.find_all('a', href=True):
                    absolute_url = urljoin(url, link['href'])
                    links.append({
                        "text": link.get_text(strip=True),
                        "url": absolute_url
                    })
                result["links"] = links

            return ToolOutput(success=True, result=result)

        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))


class HTTPRequestTool(BaseTool):
    """Make HTTP requests."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB

    @property
    def requires_approval(self) -> bool:
        return True  # Requires approval for POST/PUT/DELETE

    def execute(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> ToolOutput:
        """
        Make an HTTP request.

        Args:
            url: URL to request
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: Optional headers
            data: Optional form data
            json_data: Optional JSON data

        Returns:
            ToolOutput with response
        """
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                data=data,
                json=json_data,
                timeout=30
            )

            result = {
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "text": response.text[:1000]  # Limit response size
            }

            # Try to parse JSON
            try:
                result["json"] = response.json()
            except:
                pass

            return ToolOutput(
                success=response.status_code < 400,
                result=result
            )

        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))


class URLValidatorTool(BaseTool):
    """Validate and parse URLs."""

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB

    @property
    def requires_approval(self) -> bool:
        return False  # Read-only operation

    def execute(self, url: str) -> ToolOutput:
        """
        Validate and parse a URL.

        Args:
            url: URL to validate

        Returns:
            ToolOutput with parsed URL components
        """
        try:
            parsed = urlparse(url)

            result = {
                "valid": all([parsed.scheme, parsed.netloc]),
                "scheme": parsed.scheme,
                "netloc": parsed.netloc,
                "path": parsed.path,
                "params": parsed.params,
                "query": parsed.query,
                "fragment": parsed.fragment
            }

            return ToolOutput(success=True, result=result)

        except Exception as e:
            return ToolOutput(success=False, result=None, error=str(e))
