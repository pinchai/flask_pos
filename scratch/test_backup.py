import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backup import get_database_path, create_backup_file, format_file_size, send_db_backup_to_telegram
from app import app

class BackupTestCase(unittest.TestCase):
    def test_database_path_resolution(self):
        db_path = get_database_path()
        self.assertTrue(os.path.exists(db_path))
        self.assertTrue(db_path.endswith('.db'))

    def test_create_backup_file(self):
        backup_path = create_backup_file(output_dir="backups", compress=False)
        self.assertTrue(os.path.exists(backup_path))
        self.assertTrue(os.path.getsize(backup_path) > 0)
        # Clean up test artifact
        if os.path.exists(backup_path):
            os.remove(backup_path)

    def test_create_compressed_backup_file(self):
        backup_path = create_backup_file(output_dir="backups", compress=True)
        self.assertTrue(os.path.exists(backup_path))
        self.assertTrue(backup_path.endswith('.zip'))
        self.assertTrue(os.path.getsize(backup_path) > 0)
        # Clean up test artifact
        if os.path.exists(backup_path):
            os.remove(backup_path)

    def test_format_file_size(self):
        self.assertEqual(format_file_size(500), "500 B")
        self.assertEqual(format_file_size(2048), "2.00 KB")

    def test_flask_cli_or_route_registered(self):
        with app.test_client() as client:
            # Check route exists
            res = client.post('/backup/telegram')
            # Since unauthenticated, should redirect to login (302)
            self.assertEqual(res.status_code, 302)

if __name__ == '__main__':
    unittest.main()
