"""Small tests for the opt-in CapRover adapter."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml
import caprover


class CapRoverConfigTests(unittest.TestCase):
    def test_config_updates_database_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "config.yml"
            target.write_text(yaml.safe_dump({
                "database": {"host": "127.0.0.1", "port": 55433, "password": "old"},
                "jwt_secret": "preserve",
                "host": "127.0.0.1",
            }))
            env = {
                "YUMESUTE_DB_HOST": "srv-captain--yumesute-db",
                "YUMESUTE_DB_PASSWORD": "strong-password",
                "YUMESUTE_DB_PORT": "5432",
            }
            with patch.object(caprover, "CONFIG", target), patch.dict(os.environ, env):
                caprover.configure_database()
            result = yaml.safe_load(target.read_text())
            self.assertEqual(result["database"]["host"], env["YUMESUTE_DB_HOST"])
            self.assertEqual(result["database"]["port"], 5432)
            self.assertEqual(result["database"]["password"], env["YUMESUTE_DB_PASSWORD"])
            self.assertEqual(result["jwt_secret"], "preserve")
            self.assertEqual(result["host"], "127.0.0.1")

    def test_requires_database_host_and_password(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "config.yml"
            target.write_text(yaml.safe_dump({"database": {}}))
            with patch.object(caprover, "CONFIG", target), patch.dict(os.environ, {
                "YUMESUTE_DB_HOST": "", "YUMESUTE_DB_PASSWORD": ""
            }):
                with self.assertRaisesRegex(RuntimeError, "YUMESUTE_DB_HOST"):
                    caprover.configure_database()


if __name__ == "__main__":
    unittest.main()
