"""
Tests for Core Cleanup Engine, subfolder recursive cleanup, and safety guards.
"""

import os
import shutil
import tempfile
import unittest
from dbp_core.cleaner import perform_cleanup, get_unique_path, check_interval

class TestCleaner(unittest.TestCase):
    def setUp(self):
        self.base_dir = tempfile.mkdtemp()
        self.src_dir = os.path.join(self.base_dir, "Downloads")
        self.tgt_dir = os.path.join(self.base_dir, "Archive")
        os.makedirs(self.src_dir, exist_ok=True)
        os.makedirs(self.tgt_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.base_dir, ignore_errors=True)

    def _write_file(self, folder, relative_path, content="test content"):
        p = os.path.join(folder, relative_path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return p

    def test_recursive_subfolder_cleanup(self):
        # 1. Datei im Quellordner (Treffer)
        self._write_file(self.src_dir, "doc1.pdf")
        # 2. Datei im Quellordner (Müll)
        self._write_file(self.src_dir, "temp.junk")
        # 3. Datei im Unterordner (Treffer)
        self._write_file(self.src_dir, os.path.join("SubFolder1", "nested_doc.pdf"))
        # 4. Datei im tiefen Unterordner (Müll)
        self._write_file(self.src_dir, os.path.join("SubFolder1", "DeepSub", "deep_junk.junk"))
        # 5. Smart Trash Treffer im Unterordner
        self._write_file(self.src_dir, os.path.join("SubFolder2", "Rechnung_2026.other"))
        # 6. Aktiver Download im Quellordner (darf NICHT gelöscht werden)
        self._write_file(self.src_dir, "downloading_file.iso.crdownload")

        cfg = {
            "source_dir": self.src_dir,
            "target_dir": self.tgt_dir,
            "extensions": ".pdf",
            "smart_trash": True,
            "include_subfolders": True,
            "clean_empty_folders": True,
            "protect_recent_hours": 0,
            "max_log_size": "0.5"
        }

        logs = perform_cleanup(cfg, is_portable=False)

        # Überprüfen:
        # doc1.pdf und nested_doc.pdf müssen im Archiv liegen
        self.assertTrue(os.path.exists(os.path.join(self.tgt_dir, "doc1.pdf")))
        self.assertTrue(os.path.exists(os.path.join(self.tgt_dir, "nested_doc.pdf")))
        
        # Rechnung_2026.other muss durch Smart Trash im Archiv sein
        self.assertTrue(os.path.exists(os.path.join(self.tgt_dir, "Rechnung_2026.other")))

        # Aktiver Download muss immer noch im Quellordner liegen
        self.assertTrue(os.path.exists(os.path.join(self.src_dir, "downloading_file.iso.crdownload")))

        # temp.junk und deep_junk.junk müssen im Papierkorb liegen
        trash_dir = os.path.join(self.tgt_dir, "DBP_Trash")
        self.assertTrue(os.path.exists(os.path.join(trash_dir, "temp.junk")))
        self.assertTrue(os.path.exists(os.path.join(trash_dir, "deep_junk.junk")))

        # Leere Unterordner in Downloads müssen gelöscht worden sein
        self.assertFalse(os.path.exists(os.path.join(self.src_dir, "SubFolder1", "DeepSub")))
        self.assertFalse(os.path.exists(os.path.join(self.src_dir, "SubFolder1")))
        self.assertFalse(os.path.exists(os.path.join(self.src_dir, "SubFolder2")))

    def test_portable_mode_permanent_deletion(self):
        self._write_file(self.src_dir, "keep.pdf")
        self._write_file(self.src_dir, "junk.xyz")
        self._write_file(self.src_dir, os.path.join("SubDir", "sub_junk.xyz"))

        cfg = {
            "source_dir": self.src_dir,
            "target_dir": self.tgt_dir,
            "extensions": ".pdf",
            "smart_trash": False,
            "include_subfolders": True,
            "clean_empty_folders": True
        }

        perform_cleanup(cfg, is_portable=True)

        # keep.pdf muss archiviert sein
        self.assertTrue(os.path.exists(os.path.join(self.tgt_dir, "keep.pdf")))

        # junk-Dateien und SubDir müssen endgültig weg sein
        self.assertFalse(os.path.exists(os.path.join(self.src_dir, "junk.xyz")))
        self.assertFalse(os.path.exists(os.path.join(self.src_dir, "SubDir")))

        # Im Portable-Modus darf kein Papierkorb erstellt worden sein
        self.assertFalse(os.path.exists(os.path.join(self.tgt_dir, "DBP_Trash")))

    def test_safety_target_nested_in_source(self):
        nested_target = os.path.join(self.src_dir, "Archived_Files")
        self._write_file(self.src_dir, "doc.pdf")
        self._write_file(nested_target, "previously_archived.pdf")

        cfg = {
            "source_dir": self.src_dir,
            "target_dir": nested_target,
            "extensions": ".pdf",
            "include_subfolders": True,
            "clean_empty_folders": True
        }

        perform_cleanup(cfg, is_portable=False)

        # Das Zielverzeichnis und sein Inhalt dürfen nicht angetastet/gelöscht/doppelt verschoben werden
        self.assertTrue(os.path.exists(os.path.join(nested_target, "previously_archived.pdf")))
        self.assertTrue(os.path.exists(os.path.join(nested_target, "doc.pdf")))

    def test_unique_path_generation(self):
        self._write_file(self.tgt_dir, "report.pdf")
        new_p = get_unique_path(self.tgt_dir, "report.pdf")
        self.assertEqual(os.path.basename(new_p), "report_1.pdf")

        self._write_file(self.tgt_dir, "report_1.pdf")
        new_p2 = get_unique_path(self.tgt_dir, "report.pdf")
        self.assertEqual(os.path.basename(new_p2), "report_2.pdf")

if __name__ == "__main__":
    unittest.main()
