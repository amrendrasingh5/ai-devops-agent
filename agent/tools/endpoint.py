import socket
import ssl
import urllib.error
import urllib.request
from urllib.parse import urlparse


def investigate_endpoint(url: str, timeout: int = 10):
    """
    Collect read-only evidence about an HTTP/HTTPS endpoint.

    This function does not diagnose the problem and does not modify
    any external resources.
    """

    parsed = urlparse(url)

    hostname = parsed.hostname
    port = parsed.port

    if not hostname:
        return {
            "url": url,
            "error": "Unable to determine hostname from URL.",
        }

    if port is None:
        port = 443 if parsed.scheme == "https" else 80

    result = {
        "url": url,
        "scheme": parsed.scheme,
        "hostname": hostname,
        "port": port,
    }

    # DNS evidence
    try:
        addresses = socket.getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM,
        )

        result["dns"] = {
            "resolved": True,
            "addresses": sorted(
                {
                    address[4][0]
                    for address in addresses
                }
            ),
        }

    except socket.gaierror as exc:
        result["dns"] = {
            "resolved": False,
            "error": str(exc),
        }

    # TCP connectivity evidence
    try:
        with socket.create_connection(
            (hostname, port),
            timeout=timeout,
        ):
            result["tcp"] = {
                "reachable": True,
            }

    except Exception as exc:
        result["tcp"] = {
            "reachable": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    # HTTP/HTTPS evidence
    try:
        request = urllib.request.Request(
            url,
            method="GET",
        )

        context = ssl.create_default_context()

        with urllib.request.urlopen(
            request,
            timeout=timeout,
            context=context,
        ) as response:

            result["http"] = {
                "reachable": True,
                "status_code": response.status,
                "reason": response.reason,
                "headers": dict(response.headers),
            }

    except urllib.error.HTTPError as exc:
        result["http"] = {
            "reachable": True,
            "status_code": exc.code,
            "reason": exc.reason,
            "headers": dict(exc.headers),
        }

    except Exception as exc:
        result["http"] = {
            "reachable": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    return result
