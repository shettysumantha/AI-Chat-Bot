import unittest
from unittest.mock import patch

from database import db


class InitDbTests(unittest.TestCase):
    def test_init_db_returns_false_when_connection_fails(self):
        with patch.object(db, "get_connection", side_effect=Exception("db unavailable")):
            self.assertFalse(db.init_db())


if __name__ == "__main__":
    unittest.main()
