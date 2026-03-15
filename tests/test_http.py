"""Tests for HTTP retry module."""

import httpx
import pytest

from scripts.http import resilient_request


def test_successful_request(httpx_mock):
    """A 200 response returns immediately."""
    httpx_mock.add_response(url="https://example.com/api", json={"ok": True})
    resp = resilient_request("GET", "https://example.com/api", retries=1)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_retries_on_500(httpx_mock):
    """Retries on 500 then succeeds."""
    httpx_mock.add_response(url="https://example.com/api", status_code=500)
    httpx_mock.add_response(url="https://example.com/api", json={"ok": True})
    resp = resilient_request(
        "GET", "https://example.com/api", retries=2, backoff_base=0.01
    )
    assert resp.status_code == 200


def test_no_retry_on_404(httpx_mock):
    """404 is not retried."""
    httpx_mock.add_response(url="https://example.com/api", status_code=404)
    with pytest.raises(httpx.HTTPStatusError):
        resilient_request(
            "GET", "https://example.com/api", retries=3, backoff_base=0.01
        )
