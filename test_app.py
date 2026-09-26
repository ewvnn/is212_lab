"""Acceptance tests for "As a member, I want to borrow a duck". Run: python -m unittest"""
import unittest
from datetime import date

from app import create_app
from models import Duck, Loan, Member
from services import LOAN_PERIOD, LoanError, borrow_duck


class BorrowDuckTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(seed=False)
        self.db = self.app.extensions["db"]
        self.db.add_all([Member(member_id="M1", name="Test Member"),
                         Member(member_id="M2", name="Other Member"),
                         Duck(duck_id="D1"), Duck(duck_id="D2")])
        self.db.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        self.db.remove()

    def test_member_can_see_when_duck_is_due(self):
        today = date.today()
        response = self.client.post("/members/M1/loans", data={"duck_id": "D1"},
                                    follow_redirects=True)

        due = (today + LOAN_PERIOD).strftime("%a %d %b %Y")
        page = response.get_data(as_text=True)
        self.assertIn(f"due back on {due}", page)  # confirmation message
        self.assertIn(f"<td>{due}</td>", page)     # "My loans" table
        self.assertIn(f"Due in {LOAN_PERIOD.days} days", page)

    def test_member_with_active_loan_can_borrow_another(self):
        borrow_duck(self.db, "M1", "D1")

        response = self.client.post("/members/M1/loans", data={"duck_id": "D2"},
                                    follow_redirects=True)

        self.assertIn("approved", response.get_data(as_text=True))
        active = [loan for loan in self.db.get(Member, "M1").loans if loan.is_active]
        self.assertEqual({loan.duck_id for loan in active}, {"D1", "D2"})

    def test_duck_already_on_loan_cannot_be_borrowed(self):
        borrow_duck(self.db, "M1", "D1")

        with self.assertRaises(LoanError):
            borrow_duck(self.db, "M2", "D1")
        self.assertEqual(self.db.query(Loan).count(), 1)

    def test_returned_duck_can_be_borrowed_again(self):
        loan = borrow_duck(self.db, "M1", "D1")
        loan.return_date = date.today()
        self.db.commit()

        self.assertEqual(borrow_duck(self.db, "M2", "D1").member_id, "M2")


if __name__ == "__main__":
    unittest.main()
