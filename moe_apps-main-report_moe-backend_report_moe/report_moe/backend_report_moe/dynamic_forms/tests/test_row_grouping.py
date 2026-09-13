from django.test import SimpleTestCase

from dynamic_forms.info_confirmation import ACCEPT, WAITING
from dynamic_forms.row_grouping import (
    count_deduped_table_rows,
    group_table_rows,
    row_stats_for_infos,
    split_table_textarea_attrs,
)


class _Attr:
    def __init__(self, id, type="text", label=""):
        self.id = id
        self.type = type
        self.label = label or f"Attr {id}"


class _Info:
    def __init__(self, id, attribute_id, user_id, value, confirmed=WAITING):
        self.id = id
        self.attribute_id = attribute_id
        self.user_id = user_id
        self.value = value
        self.confirmed = confirmed
        self.commit_note = ""
        self.confirm_note = ""


class RowGroupingTests(SimpleTestCase):
    def test_single_submit_fills_one_row(self):
        attrs = [_Attr(1), _Attr(2), _Attr(3)]
        infos = [
            _Info(1, 1, 10, "a"),
            _Info(2, 2, 10, "b"),
            _Info(3, 3, 10, "c"),
        ]
        table_attrs, _ = split_table_textarea_attrs(attrs)
        rows = group_table_rows(infos, table_attrs)
        self.assertEqual(count_deduped_table_rows(infos, table_attrs), 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["attr_1"], "a")
        self.assertEqual(len(rows[0]["_info_ids"]), 3)

    def test_two_users_two_rows(self):
        attrs = [_Attr(1), _Attr(2)]
        infos = [
            _Info(1, 1, 10, "u1a"),
            _Info(2, 2, 10, "u1b"),
            _Info(3, 1, 20, "u2a"),
            _Info(4, 2, 20, "u2b"),
        ]
        table_attrs, _ = split_table_textarea_attrs(attrs)
        self.assertEqual(count_deduped_table_rows(infos, table_attrs), 2)

    def test_row_confirmation_stats(self):
        attrs = [_Attr(1), _Attr(2)]
        infos = [
            _Info(1, 1, 10, "a", confirmed=ACCEPT),
            _Info(2, 2, 10, "b", confirmed=WAITING),
            _Info(3, 1, 20, "c", confirmed=ACCEPT),
            _Info(4, 2, 20, "d", confirmed=ACCEPT),
        ]
        stats = row_stats_for_infos(infos, attrs)
        self.assertEqual(stats["rows_count"], 2)
        self.assertEqual(stats["rows_confirmed_count"], 1)
        self.assertEqual(stats["rows_pending_count"], 1)
