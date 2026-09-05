import datetime
import unittest

from backend.ingest import normalize as norm


class TestNormalize(unittest.TestCase):
    def test_parse_iso_date(self):
        self.assertEqual(norm.parse_iso_date("2023-04-01"), datetime.date(2023, 4, 1))
        self.assertIsNone(norm.parse_iso_date(None))

    def test_parse_iso_datetime_variable_fraction_length(self):
        self.assertEqual(
            norm.parse_iso_datetime("2024-02-19T22:00:00.0"),
            datetime.datetime(2024, 2, 19, 22, 0, 0),
        )
        self.assertEqual(
            norm.parse_iso_datetime("2023-04-01T13:03:39.300"),
            datetime.datetime(2023, 4, 1, 13, 3, 39, 300000),
        )

    def test_parse_epoch_ms(self):
        self.assertEqual(norm.parse_epoch_ms(1680307200000), datetime.datetime(2023, 4, 1, 0, 0, 0))

    def test_parse_epoch_ms_date_rejects_non_int(self):
        with self.assertRaises(TypeError):
            norm.parse_epoch_ms_date("2023-04-01")

    def test_parse_epoch_ms_date_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            norm.parse_epoch_ms_date(123)

    def test_parse_java_date_tostring(self):
        self.assertEqual(
            norm.parse_java_date_tostring("Thu Aug 06 22:00:00 GMT 2026"),
            datetime.datetime(2026, 8, 6, 22, 0, 0),
        )

    def test_unit_converters(self):
        self.assertAlmostEqual(norm.cm_to_m(508558.984375), 5085.58984375)
        self.assertAlmostEqual(norm.ms_to_s(1721529.052734375), 1721.529052734375)
        self.assertAlmostEqual(norm.cmms_to_mps(0.2953999996185303), 2.953999996185303)
        self.assertIsNone(norm.cm_to_m(None))

    def test_none_if_zero(self):
        self.assertIsNone(norm.none_if_zero(0))
        self.assertEqual(norm.none_if_zero(5), 5)


if __name__ == "__main__":
    unittest.main()
