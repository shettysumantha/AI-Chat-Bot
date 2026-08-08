import unittest
from unittest.mock import patch

from database import db


class InitDbTests(unittest.TestCase):
    def test_init_db_returns_false_when_connection_fails(self):
        with patch.object(db, "get_connection", side_effect=Exception("db unavailable")):
            self.assertFalse(db.init_db())

    def test_create_user_returns_none_when_connection_fails(self):
        with patch.object(db, "get_connection", side_effect=Exception("db unavailable")):
            self.assertIsNone(db.create_user("Jane", "jane@example.com", None, "hash"))

    def test_get_user_by_email_returns_none_when_connection_fails(self):
        with patch.object(db, "get_connection", side_effect=Exception("db unavailable")):
            self.assertIsNone(db.get_user_by_email("jane@example.com"))

    def test_update_user_password_returns_false_when_connection_fails(self):
        with patch.object(db, "get_connection", side_effect=Exception("db unavailable")):
            self.assertFalse(db.update_user_password("jane@example.com", "hash"))

if __name__ == "__main__":
    unittest.main()
