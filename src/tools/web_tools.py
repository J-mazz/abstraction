"""
Tools for web tasks with built-in URL safety checks.
"""
from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, Iterable, List
from urllib.parse import urljoin, urlparse, ParseResult
from .base import BaseTool, ToolCategory, ToolOutput


def _normalize_hosts(hosts: Optional[Iterable[str]]) -> List[str]:
    if not hosts:
        return []
    normalized = []
    for host in hosts:
        if not host:
            continue
        host = host.strip().lower()
        if host:
            normalized.append(host)
    return normalized


class _URLSafetyMixin:
    """Common URL validation helpers for HTTP tools."""

    def __init__(self, allowed_hosts: Optional[Iterable[str]] = None):
        self._allowed_hosts = _normalize_hosts(allowed_hosts)
        self._allowed_schemes = {"http", "https"}

    def _host_allowed(self, hostname: str) -> bool:
        if not hostname:
            return False
        hostname = hostname.lower()
        if not self._allowed_hosts:
            return True

        for allowed in self._allowed_hosts:
            if allowed.startswith('*.'):
                suffix = allowed[1:]
                if hostname.endswith(suffix) or hostname == suffix.lstrip('.'):
                    return True
            elif hostname == allowed:
                return True
        return False

    def _validate_url(self, url: str) -> ParseResult:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in self._allowed_schemes:
            raise ValueError(f"Unsupported URL scheme '{parsed.scheme}'")
        if not parsed.hostname:
            raise ValueError("URL must include a hostname")
        if not self._host_allowed(parsed.hostname):
            raise ValueError(f"Host '{parsed.hostname}' is not allowlisted")
        return parsed


class WebScraperTool(_URLSafetyMixin, BaseTool):
    """Scrape content from a web page while enforcing URL safety policies."""

    def __init__(self, allowed_hosts: Optional[Iterable[str]] = None, timeout: int = 30):
        BaseTool.__init__(self)
        _URLSafetyMixin.__init__(self, allowed_hosts)
        self._timeout = timeout

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
            parsed = self._validate_url(url)
            response = requests.get(url, timeout=self._timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            result = {
                "url": url,
                "status_code": response.status_code,
                "title": soup.title.string if soup.title else None,
                "hostname": parsed.hostname,
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


class HTTPRequestTool(_URLSafetyMixin, BaseTool):
    """Make HTTP requests with hostname allowlisting."""

    def __init__(self, allowed_hosts: Optional[Iterable[str]] = None, timeout: int = 30):
        BaseTool.__init__(self)
        _URLSafetyMixin.__init__(self, allowed_hosts)
        self._timeout = timeout

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
            parsed = self._validate_url(url)
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                data=data,
                json=json_data,
                timeout=self._timeout
            )

            result = {
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "text": response.text[:1000],  # Limit response size
                "hostname": parsed.hostname,
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
