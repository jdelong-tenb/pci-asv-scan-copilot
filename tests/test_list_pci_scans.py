import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import list_pci_scans as m  # noqa: E402


class TemplateKindTests(unittest.TestCase):
    def test_asv_is_submittable(self):
        self.assertEqual(m.template_kind({"name": "asv", "title": "PCI Quarterly External Scan"}), "asv")

    def test_pci_is_internal(self):
        self.assertEqual(m.template_kind({"name": "pci", "title": "Internal PCI Network Scan"}), "pci")

    def test_unrelated_template(self):
        self.assertIsNone(m.template_kind({"name": "basic", "title": "Basic Network Scan"}))

    def test_other_pci_template(self):
        self.assertEqual(m.template_kind({"name": "pci_other", "title": "Something"}), "other")
        self.assertEqual(m.template_kind({"name": "x", "title": "Custom PCI Thing"}), "other")

    def test_template_without_names(self):
        self.assertIsNone(m.template_kind({}))
        self.assertIsNone(m.template_kind({"name": None, "title": None}))

    def test_scan_name_match(self):
        self.assertTrue(m.is_pci_scan_name("Q3 ASV"))
        self.assertFalse(m.is_pci_scan_name("Weekly"))
        self.assertFalse(m.is_pci_scan_name(None))


if __name__ == "__main__":
    unittest.main()
