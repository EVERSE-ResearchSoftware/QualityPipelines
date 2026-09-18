import unittest

from resqui.vocabulary import fetch_known_indicator_ids, is_known_indicator_id


class TestVocabulary(unittest.TestCase):
    def test_fetches_known_ids_from_everse_api(self):
        known_ids = fetch_known_indicator_ids()
        self.assertIsInstance(known_ids, frozenset)
        self.assertGreater(len(known_ids), 0)
        self.assertTrue(
            all(
                uid.startswith("https://w3id.org/everse/i/indicators/")
                for uid in known_ids
            )
        )

    def test_missing_sentinel_is_always_known(self):
        self.assertTrue(is_known_indicator_id("missing"))

    def test_known_id_from_vocabulary(self):
        known_ids = fetch_known_indicator_ids()
        sample_id = next(iter(known_ids))
        self.assertTrue(is_known_indicator_id(sample_id))

    def test_unknown_id_is_rejected(self):
        self.assertFalse(
            is_known_indicator_id("https://w3id.org/everse/i/indicators/citation")
        )

    def test_known_license_and_citation_ids(self):
        self.assertTrue(
            is_known_indicator_id(
                "https://w3id.org/everse/i/indicators/software_has_license"
            )
        )
        self.assertTrue(
            is_known_indicator_id(
                "https://w3id.org/everse/i/indicators/software_has_citation"
            )
        )
        self.assertTrue(
            is_known_indicator_id("https://w3id.org/everse/i/indicators/has_ci-tests")
        )


if __name__ == "__main__":
    unittest.main()
