from django.test import SimpleTestCase

from dynamic_forms.info_rows_pagination import (
    clamp_page_args,
    decode_row_cursor,
    encode_row_cursor,
)


class ClampPageArgsTests(SimpleTestCase):
    def test_defaults_and_bounds(self):
        self.assertEqual(clamp_page_args(None, None), (1, 20))
        self.assertEqual(clamp_page_args("2", "50"), (2, 50))
        self.assertEqual(clamp_page_args(0, 500), (1, 100))
        self.assertEqual(clamp_page_args("x", "y"), (1, 20))


class RowCursorTests(SimpleTestCase):
    def test_roundtrip(self):
        token = encode_row_cursor(
            "2026-09-08T10:00:00+00:00", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        decoded = decode_row_cursor(token)
        self.assertIsNotNone(decoded)
        dt, key = decoded
        self.assertEqual(key, "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        self.assertEqual(dt.isoformat(), "2026-09-08T10:00:00+00:00")

    def test_invalid(self):
        self.assertIsNone(decode_row_cursor(None))
        self.assertIsNone(decode_row_cursor("not-valid"))
