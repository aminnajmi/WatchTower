import unittest

from app.integrations.tidio_browser import _conversation_id_from_url


class TidioBrowserParsingTests(unittest.TestCase):
    def test_conversation_id_from_absolute_url(self):
        self.assertEqual(
            _conversation_id_from_url("https://www.tidio.com/panel/conversations/abc123"),
            "abc123",
        )

    def test_conversation_id_from_relative_url_with_query(self):
        self.assertEqual(
            _conversation_id_from_url("/panel/conversations/42?foo=bar"),
            "42",
        )

    def test_non_conversation_url(self):
        self.assertIsNone(_conversation_id_from_url("https://www.tidio.com/panel/inbox"))


if __name__ == "__main__":
    unittest.main()
