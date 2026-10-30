"""
Tests for Smart Trash functionality and in-progress download protection.
"""

import os
import time
import tempfile
import unittest
from dbp_core.smart_trash import (
    evaluate_file_importance,
    is_in_progress_download,
    is_system_metadata_file
)

class TestSmartTrash(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_file(self, filename, content="dummy content", age_seconds=0):
        p = os.path.join(self.test_dir, filename)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        if age_seconds > 0:
            past_time = time.time() - age_seconds
            os.utime(p, (past_time, past_time))
        return p

    def test_in_progress_downloads(self):
        p1 = self._create_file("document.pdf.crdownload")
        p2 = self._create_file("archive.zip.part")
        p3 = self._create_file("~$WordDocument.docx")

        self.assertTrue(is_in_progress_download(p1))
        self.assertTrue(is_in_progress_download(p2))
        self.assertTrue(is_in_progress_download(p3))

        is_imp, reason, is_active = evaluate_file_importance(p1)
        self.assertTrue(is_active)
        self.assertFalse(is_imp)

    def test_important_keywords(self):
        p1 = self._create_file("Rechnung_Telekom_Oktober.other")
        p2 = self._create_file("steuerbescheid_2025.dat")
        p3 = self._create_file("my_employment_contract.bin")

        is_imp1, reason1, _ = evaluate_file_importance(p1, protect_recent_hours=0)
        is_imp2, reason2, _ = evaluate_file_importance(p2, protect_recent_hours=0)
        is_imp3, reason3, _ = evaluate_file_importance(p3, protect_recent_hours=0)

        self.assertTrue(is_imp1)
        self.assertIn("rechnung", reason1.lower())
        self.assertTrue(is_imp2)
        self.assertIn("steuer", reason2.lower())
        self.assertTrue(is_imp3)
        self.assertIn("contract", reason3.lower())

    def test_important_extensions(self):
        p_py = self._create_file("script.py", age_seconds=100000)
        p_csv = self._create_file("data.csv", age_seconds=100000)
        p_odt = self._create_file("notes.odt", age_seconds=100000)

        is_imp1, _, _ = evaluate_file_importance(p_py, protect_recent_hours=0)
        is_imp2, _, _ = evaluate_file_importance(p_csv, protect_recent_hours=0)
        is_imp3, _, _ = evaluate_file_importance(p_odt, protect_recent_hours=0)

        self.assertTrue(is_imp1)
        self.assertTrue(is_imp2)
        self.assertTrue(is_imp3)

    def test_junk_extensions(self):
        p_tmp = self._create_file("cache.tmp")
        p_old = self._create_file("backup.old")

        is_imp1, reason1, _ = evaluate_file_importance(p_tmp)
        is_imp2, reason2, _ = evaluate_file_importance(p_old)

        self.assertFalse(is_imp1)
        self.assertIn("Junk", reason1)
        self.assertFalse(is_imp2)
        self.assertIn("Junk", reason2)

    def test_recent_file_grace_period(self):
        p_recent = self._create_file("custom_tool.xyz", age_seconds=3600)  # 1 Stunde alt
        p_old = self._create_file("custom_tool_old.xyz", age_seconds=100000)  # ~28 Stunden alt

        is_imp_recent, reason_recent, _ = evaluate_file_importance(p_recent, protect_recent_hours=24)
        is_imp_old, reason_old, _ = evaluate_file_importance(p_old, protect_recent_hours=24)

        self.assertTrue(is_imp_recent)
        self.assertIn("Recent", reason_recent)
        self.assertFalse(is_imp_old)

if __name__ == "__main__":
    unittest.main()
