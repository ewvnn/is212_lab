"""Acceptance tests, one class per user story (see README). Run: python -m unittest"""
import unittest
from datetime import date, timedelta

from app import create_app
from models import DeluxeDuck, Loan, Member, StandardDuck
from services import LoanError, borrow_duck, return_duck


def fmt(d: date) -> str:
    return d.strftime("%a %d %b %Y")


class LibraryTestCase(unittest.TestCase):
    """Two members, two standard ducks (D1, D2) and one Deluxe duck (X1)."""

    def setUp(self):
        self.app = create_app(seed=False)
        self.db = self.app.extensions["db"]
        self.db.add_all([Member(member_id="M1", name="Test Member"),
                         Member(member_id="M2", name="Other Member"),
                         StandardDuck(duck_id="D1"), StandardDuck(duck_id="D2"),
                         DeluxeDuck(duck_id="X1")])
        self.db.commit()
        self.client = self.app.test_client()
        self.today = date.today()

    def tearDown(self):
        engine = self.db.get_bind()
        self.db.remove()
        engine.dispose()

    def borrow_via_page(self, member_id, duck_id) -> str:
        response = self.client.post(f"/members/{member_id}/loans", data={"duck_id": duck_id},
                                    follow_redirects=True)
        return response.get_data(as_text=True)

    def return_via_page(self, member_id, loan_id) -> str:
        response = self.client.post(f"/members/{member_id}/loans/{loan_id}/return",
                                    follow_redirects=True)
        return response.get_data(as_text=True)


class BorrowDuckTest(LibraryTestCase):
    """US1: As a member, I want to borrow a duck from the library."""

    def test_member_can_see_when_duck_is_due(self):
        page = self.borrow_via_page("M1", "D1")

        due = fmt(self.today + timedelta(days=7))
        self.assertIn(f"due back on {due}", page)  # confirmation message
        self.assertIn(f"<td>{due}</td>", page)     # "My loans" table
        self.assertIn("Due in 7 days", page)

    def test_member_with_active_loan_can_borrow_another(self):
        borrow_duck(self.db, "M1", "D1")

        page = self.borrow_via_page("M1", "D2")

        self.assertIn("approved", page)
        active = [loan for loan in self.db.get(Member, "M1").loans if loan.is_active]
        self.assertEqual({loan.duck_id for loan in active}, {"D1", "D2"})

    def test_duck_already_on_loan_cannot_be_borrowed(self):
        borrow_duck(self.db, "M1", "D1")

        with self.assertRaises(LoanError):
            borrow_duck(self.db, "M2", "D1")
        self.assertEqual(self.db.query(Loan).count(), 1)


class DeluxeLoanPeriodTest(LibraryTestCase):
    """US2: As a member, I want to borrow a Deluxe duck for 14 days,
    so that I can keep the extra motivation for longer."""

    def test_deluxe_duck_is_due_back_in_14_days(self):
        page = self.borrow_via_page("M1", "X1")

        due = fmt(self.today + timedelta(days=14))
        self.assertIn(f"due back on {due}", page)
        self.assertIn("Due in 14 days", page)
        self.assertEqual(self.db.get(Loan, "L0001").due_date, self.today + timedelta(days=14))

    def test_standard_duck_is_still_due_back_in_7_days(self):
        loan = borrow_duck(self.db, "M1", "D1")

        self.assertEqual(loan.due_date, self.today + timedelta(days=7))

    def test_member_sees_each_ducks_type_and_due_date_before_borrowing(self):
        page = self.client.get("/members/M1").get_data(as_text=True)

        self.assertIn("<td>Deluxe</td>", page)
        self.assertIn("<td>Standard</td>", page)
        self.assertIn(fmt(self.today + timedelta(days=14)), page)
        self.assertIn(fmt(self.today + timedelta(days=7)), page)


class DeluxeDepositTest(LibraryTestCase):
    """US3: As a member, I want to know the deposit for a Deluxe duck and see that it is
    held on my loan, so that I know what I am paying and that I will get it back."""

    def test_deposit_is_shown_before_borrowing(self):
        page = self.client.get("/members/M1").get_data(as_text=True)

        self.assertIn("$5.00 <span class=\"muted\">(refundable)</span>", page)

    def test_borrowing_a_deluxe_duck_holds_its_deposit(self):
        page = self.borrow_via_page("M1", "X1")

        self.assertEqual(self.db.get(Loan, "L0001").deposit_held, 5.00)
        self.assertIn("A deposit of $5.00 is held", page)  # confirmation message
        self.assertIn("$5.00 held", page)                  # "My loans" table

    def test_standard_duck_needs_no_deposit(self):
        page = self.borrow_via_page("M1", "D1")

        self.assertEqual(self.db.get(Loan, "L0001").deposit_held, 0.0)
        self.assertNotIn("deposit of", page)

    def test_deposit_follows_the_ducks_own_amount(self):
        self.db.add(DeluxeDuck(duck_id="X2", deposit_amount=8.50))
        self.db.commit()

        self.assertEqual(borrow_duck(self.db, "M1", "X2").deposit_held, 8.50)


class ReturnDuckTest(LibraryTestCase):
    """US4: As a member, I want to return a duck, so that my deposit is refunded
    and the duck is free for someone else."""

    def test_returning_a_deluxe_duck_refunds_the_deposit(self):
        borrow_duck(self.db, "M1", "X1")

        page = self.return_via_page("M1", "L0001")

        self.assertIn("Your $5.00 deposit has been refunded", page)
        self.assertIn("$5.00 refunded", page)
        self.assertIn(f"Returned {fmt(self.today)}", page)
        self.assertEqual(self.db.get(Loan, "L0001").return_date, self.today)

    def test_returning_a_standard_duck_mentions_no_deposit(self):
        borrow_duck(self.db, "M1", "D1")

        page = self.return_via_page("M1", "L0001")

        self.assertIn("Duck D1 returned", page)
        self.assertNotIn("refunded", page)

    def test_returned_duck_can_be_borrowed_again(self):
        loan = borrow_duck(self.db, "M1", "D1")
        return_duck(self.db, "M1", loan.loan_id)

        self.assertEqual(borrow_duck(self.db, "M2", "D1").member_id, "M2")

    def test_loan_cannot_be_returned_twice(self):
        loan = borrow_duck(self.db, "M1", "X1")
        return_duck(self.db, "M1", loan.loan_id)

        with self.assertRaises(LoanError):
            return_duck(self.db, "M1", loan.loan_id)

    def test_member_cannot_return_someone_elses_loan(self):
        loan = borrow_duck(self.db, "M1", "D1")

        page = self.return_via_page("M2", loan.loan_id)

        self.assertIn("Member M2 has no loan L0001", page)
        self.assertTrue(self.db.get(Loan, loan.loan_id).is_active)


if __name__ == "__main__":
    unittest.main()
