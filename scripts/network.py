"""Small bounded HTTPS client: exact-host redirects and public DNS only."""
from __future__ import annotations

import ipaddress
import socket
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from .catalog import canonical_url

MAX_BYTES = 5_000_000


def validate_target(url, allowed_hosts=None):
    canonical_url(url)
    host = (urlsplit(url).hostname or "").lower().rstrip(".")
    if allowed_hosts is not None and host not in set(allowed_hosts):
        raise ValueError("Redirect or URL is outside the source host allowlist")
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(result[4][0]).is_global for result in addresses):
        raise ValueError("Source resolves to a non-public address")


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_hosts):
        super().__init__()
        self.allowed_hosts = allowed_hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_target(newurl, self.allowed_hosts)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, allowed_hosts=None):
    validate_target(url, allowed_hosts)
    opener = urllib.request.build_opener(SafeRedirect(allowed_hosts))
    request = urllib.request.Request(url, headers={
        "User-Agent": "AI-Olami/2.0 (+https://ismoilovmuxammadyusuf5-rgb.github.io/ai-olami/)",
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/html;q=0.9, */*;q=0.5",
        "Accept-Encoding": "identity",
    })
    for attempt in range(2):
        try:
            with opener.open(request, timeout=12) as response:
                validate_target(response.geturl(), allowed_hosts)
                if int(response.headers.get("Content-Length", "0")) > MAX_BYTES:
                    raise ValueError("Source exceeds size limit")
                content = response.read(MAX_BYTES + 1)
                if len(content) > MAX_BYTES:
                    raise ValueError("Source exceeds size limit")
                return content, response.geturl()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            # Permanent HTTP refusals are not hammered; transient failures retry.
            if isinstance(error, urllib.error.HTTPError) and error.code < 500 and error.code != 429:
                raise
            if attempt:
                raise
            time.sleep(0.4)
    raise RuntimeError("Unreachable fetch state")
