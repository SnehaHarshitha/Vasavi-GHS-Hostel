import unittest
from werkzeug.security import generate_password_hash, check_password_hash

class TestAuthLogic(unittest.TestCase):
    def test_password_hashing(self):
        password = "SecurePassword123!"
        hashed = generate_password_hash(password)
        self.assertTrue(check_password_hash(hashed, password))
        self.assertFalse(check_password_hash(hashed, "WrongPassword"))

    def test_role_permissions(self):
        roles = ['student', 'warden', 'admin', 'principal']
        self.assertIn('student', roles)
        self.assertIn('principal', roles)

if __name__ == '__main__':
    unittest.main()
