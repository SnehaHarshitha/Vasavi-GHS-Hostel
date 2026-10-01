import unittest
from app.models.sick_leave_model import SickLeaveModel

class TestSickLeaveLogic(unittest.TestCase):
    def test_sick_leave_reasons(self):
        self.assertIn('Fever / Flu', SickLeaveModel.REASONS)
        self.assertIn('Stomach Ache / Food Poisoning', SickLeaveModel.REASONS)

    def test_sick_leave_statuses(self):
        self.assertIn('Submitted', SickLeaveModel.STATUSES)
        self.assertIn('Approved by Warden', SickLeaveModel.STATUSES)
        self.assertIn('Approved by Principal', SickLeaveModel.STATUSES)
        self.assertIn('Rejected', SickLeaveModel.STATUSES)

if __name__ == '__main__':
    unittest.main()
