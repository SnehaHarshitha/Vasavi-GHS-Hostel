import unittest

class TestMessLogic(unittest.TestCase):
    def test_food_choice_validation(self):
        valid_choices = ['egg', 'veg']
        self.assertIn('egg', valid_choices)
        self.assertIn('veg', valid_choices)
        self.assertNotIn('chicken', valid_choices)

    def test_choice_days(self):
        applicable_days = ['Thursday', 'Friday']
        self.assertTrue('Thursday' in applicable_days)
        self.assertTrue('Friday' in applicable_days)
        self.assertFalse('Monday' in applicable_days)

if __name__ == '__main__':
    unittest.main()
