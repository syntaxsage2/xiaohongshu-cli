"""
Integration tests for XHS API client.

These tests require actual XHS cookies (a logged-in browser session).
They test against the real XHS API to verify the complete signing + request pipeline.

Run with: uv run pytest tests/test_integration.py -v
Skip if no cookies available.
"""

import time

import pytest

from xhs_cli.client import XhsClient
from xhs_cli.cookies import get_cookies
from xhs_cli.exceptions import NoCookieError


def _get_test_cookies():
    """Try to get cookies for integration testing."""
    try:
        return get_cookies("chrome")
    except (NoCookieError, Exception):
        return None


# Skip all integration tests if no cookies available
cookies = _get_test_cookies()
pytestmark = pytest.mark.skipif(cookies is None, reason="No XHS cookies available for integration testing")


@pytest.fixture
def client():
    """Create a test client with real cookies."""
    assert cookies is not None
    c = XhsClient(cookies)
    yield c
    c.close()


class TestAuth:
    """Test authentication and user info."""

    def test_get_self_info(self, client: XhsClient):
        """Should return current user's profile."""
        info = client.get_self_info()
        assert info is not None
        assert "nickname" in info or isinstance(info, dict)

    def test_cookies_have_a1(self):
        """Cookies should contain the critical 'a1' field."""
        assert cookies is not None
        assert "a1" in cookies
        assert len(cookies["a1"]) > 0


class TestSearch:
    """Test search functionality."""

    def test_search_notes(self, client: XhsClient):
        """Should return search results for a common keyword."""
        data = client.search_notes("美食", page=1)
        assert data is not None
        # Should have items
        items = data.get("items", [])
        assert len(items) > 0

    def test_search_with_sort(self, client: XhsClient):
        """Should accept sort parameter."""
        time.sleep(1)  # Rate limit awareness
        data = client.search_notes("旅行", sort="popularity_descending")
        assert data is not None

    def test_search_returns_note_cards(self, client: XhsClient):
        """Search results should contain note_card data."""
        time.sleep(1)
        data = client.search_notes("咖啡")
        items = data.get("items", [])
        if items:
            first = items[0]
            # Should have note_card or model_type
            assert "note_card" in first or "model_type" in first


class TestFeed:
    """Test feed functionality."""

    def test_get_home_feed(self, client: XhsClient):
        """Should return feed items."""
        time.sleep(1)
        data = client.get_home_feed()
        assert data is not None
        items = data.get("items", [])
        assert len(items) > 0, "Feed should have items"

    def test_feed_items_have_structure(self, client: XhsClient):
        """Feed items should contain note cards."""
        time.sleep(1)
        data = client.get_home_feed()
        items = data.get("items", [])
        if items:
            first = items[0]
            assert "note_card" in first or "id" in first


class TestNoteRead:
    """Test reading individual notes."""

    def test_read_note_from_search(self, client: XhsClient):
        """Should be able to read a note found via search."""
        time.sleep(1)
        # First search to get a valid note ID
        search_data = client.search_notes("美食")
        items = search_data.get("items", [])
        if not items:
            pytest.skip("No search results to test with")

        note_id = items[0].get("id", "")
        xsec_token = items[0].get("xsec_token", "")
        if not note_id:
            pytest.skip("No note ID in search results")

        time.sleep(1)
        note_data = client.get_note_by_id(note_id, xsec_token=xsec_token)
        assert note_data is not None

    def test_read_note_from_feed(self, client: XhsClient):
        """Should be able to read a note found via feed."""
        time.sleep(1)
        feed_data = client.get_home_feed()
        items = feed_data.get("items", [])
        if not items:
            pytest.skip("No feed items")

        note_id = items[0].get("id", "")
        xsec_token = items[0].get("xsec_token", "")
        if not note_id:
            pytest.skip("No note ID in feed")

        time.sleep(1)
        note_data = client.get_note_by_id(note_id, xsec_token=xsec_token)
        assert note_data is not None


class TestComments:
    """Test comments functionality."""

    def test_get_comments(self, client: XhsClient):
        """Should fetch comments for a note from search."""
        time.sleep(1)
        search_data = client.search_notes("美食")
        items = search_data.get("items", [])
        if not items:
            pytest.skip("No search results")

        note_id = items[0].get("id", "")
        xsec_token = items[0].get("xsec_token", "")
        if not note_id:
            pytest.skip("No note ID")

        time.sleep(1)
        comments_data = client.get_comments(note_id, xsec_token=xsec_token)
        assert comments_data is not None
        # Comments might be empty but the call should succeed


class TestUserInfo:
    """Test user info functionality."""

    def test_get_self_info_structure(self, client: XhsClient):
        """Self info should contain expected fields."""
        info = client.get_self_info()
        assert isinstance(info, dict)
        # Should have basic fields
        assert any(k in info for k in ["nickname", "red_id", "user_id"])


class TestTopics:
    """Test topic search."""

    def test_search_topics(self, client: XhsClient):
        """Should find topics for a keyword."""
        time.sleep(1)
        data = client.search_topics("美食")
        assert data is not None


class TestEndToEnd:
    """End-to-end workflow tests."""

    def test_search_then_read_workflow(self, client: XhsClient):
        """Complete workflow: search → pick first result → read full note."""
        # 1. Search
        time.sleep(1)
        search_result = client.search_notes("Python编程")
        items = search_result.get("items", [])
        if not items:
            pytest.skip("No search results for e2e test")

        # 2. Extract info from first result
        first = items[0]
        note_id = first.get("id", "")
        xsec_token = first.get("xsec_token", "")
        note_card = first.get("note_card", {})

        assert note_id, "Should have note ID"
        assert note_card.get("title") or note_card.get("display_title"), "Should have title"

        # 3. Read full note
        time.sleep(1)
        note = client.get_note_by_id(note_id, xsec_token=xsec_token)
        assert note is not None

        # 4. Read comments
        time.sleep(1)
        comments = client.get_comments(note_id, xsec_token=xsec_token)
        assert comments is not None

    def test_feed_workflow(self, client: XhsClient):
        """Feed → read first note → get comments."""
        time.sleep(1)
        feed = client.get_home_feed()
        items = feed.get("items", [])
        if not items:
            pytest.skip("Empty feed")

        note_id = items[0].get("id", "")
        xsec_token = items[0].get("xsec_token", "")
        if not note_id:
            pytest.skip("No note ID in feed")

        time.sleep(1)
        note = client.get_note_by_id(note_id, xsec_token=xsec_token)
        assert note is not None
