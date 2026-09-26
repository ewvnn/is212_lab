"""Borrowing rules, kept separate from the web layer so they are easy to test."""
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Duck, Loan, Member


class LoanError(Exception):
    """A borrow or return request that cannot be approved."""


def available_ducks(session: Session) -> list[Duck]:
    """Ducks with no active (unreturned) loan."""
    stmt = (
        select(Duck)
        .where(~Duck.loans.any(Loan.return_date.is_(None)))
        .order_by(Duck.duck_id)
    )
    return list(session.scalars(stmt))


def due_date_for(duck: Duck, borrow_date: date) -> date:
    return borrow_date + timedelta(days=duck.loan_period_days)


def borrow_duck(session: Session, member_id: str, duck_id: str, today: date | None = None) -> Loan:
    today = today or date.today()

    member = session.get(Member, member_id)
    if member is None:
        raise LoanError(f"No member with ID {member_id}.")
    duck = session.get(Duck, duck_id)
    if duck is None:
        raise LoanError(f"No duck with ID {duck_id}.")
    if duck.current_loan is not None:
        raise LoanError(f"Duck {duck_id} is already on loan.")

    # Deliberately no cap on a member's active loans: a member who already
    # has a duck out may borrow another one.
    loan = Loan(
        loan_id=_next_loan_id(session),
        member=member,
        duck=duck,
        borrow_date=today,
        # Standard and Deluxe ducks differ only in these two values.
        due_date=due_date_for(duck, today),
        deposit_held=duck.required_deposit,
    )
    session.add(loan)
    session.commit()
    return loan


def return_duck(session: Session, member_id: str, loan_id: str, today: date | None = None) -> Loan:
    """Close a member's active loan. Any deposit held on it is refunded in full."""
    today = today or date.today()

    loan = session.get(Loan, loan_id)
    if loan is None or loan.member_id != member_id:
        raise LoanError(f"Member {member_id} has no loan {loan_id}.")
    if not loan.is_active:
        raise LoanError(f"Loan {loan_id} was already returned.")

    loan.return_date = today
    session.commit()
    return loan


def _next_loan_id(session: Session) -> str:
    count = session.scalar(select(func.count()).select_from(Loan))
    return f"L{count + 1:04d}"
