"""
Tests for configuration loading and persistence.
"""

import os
import shutil
import tempfile
import unittest
from dbp_core import config
from dbp_core.constants import DEFAULT_CONFIG

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.orig_dbp_dir = config.DBP_DIR
        self.orig_config_file = config.CONFIG_FILE
        config.DBP_DIR = self.temp_dir
        config.CONFIG_FILE = os.path.join(self.temp_dir, "config.json")

    def tearDown(self):
        config.DBP_DIR = self.orig_dbp_dir
        config.CONFIG_FILE = self.orig_config_file
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_default_config(self):
        cfg = config.load_config()
        self.assertEqual(cfg["language"], "English")
        self.assertTrue(cfg["smart_trash"])
        self.assertTrue(cfg["include_subfolders"])
        self.assertTrue(cfg["clean_empty_folders"])

    def test_save_and_reload_config(self):
        cfg = config.load_config()
        cfg["language"] = "Deutsch"
        cfg["source_dir"] = r"C:\TestDownloads"
        cfg["target_dir"] = r"C:\TestArchive"
        cfg["smart_trash"] = True
        cfg["include_subfolders"] = True

        config.save_config(cfg)
        loaded = config.load_config()

        self.assertEqual(loaded["language"], "Deutsch")
        self.assertEqual(loaded["source_dir"], r"C:\TestDownloads")
        self.assertEqual(loaded["target_dir"], r"C:\TestArchive")
        self.assertTrue(loaded["smart_trash"])

if __name__ == "__main__":
    unittest.main()
