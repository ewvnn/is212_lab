"""Rubber-duck lending library prototype. Run with:  python app.py"""
from datetime import date, timedelta

from flask import Flask, abort, flash, redirect, render_template, request, url_for
from sqlalchemy import create_engine, select
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, DeluxeDuck, Loan, Member, StandardDuck
from services import LoanError, available_ducks, borrow_duck, due_date_for, return_duck


def create_app(seed: bool = True) -> Flask:
    app = Flask(__name__)
    app.secret_key = "prototype-only"  # needed for flash messages

    # One shared connection, so every request sees the same in-memory database.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    db = scoped_session(sessionmaker(bind=engine))
    app.extensions["db"] = db

    if seed:
        seed_data(db())

    @app.teardown_appcontext
    def remove_session(exc):
        db.remove()

    @app.template_filter("fmt")
    def format_date(d: date) -> str:
        return d.strftime("%a %d %b %Y")

    @app.template_filter("money")
    def format_money(amount: float) -> str:
        return f"${amount:.2f}"

    @app.template_global()
    def loan_status(loan: Loan, today: date) -> tuple[str, str]:
        """(label, css class) describing when a loan is due back."""
        if not loan.is_active:
            return f"Returned {format_date(loan.return_date)}", "returned"
        days = (loan.due_date - today).days
        if days > 1:
            return f"Due in {days} days", "ok"
        if days == 1:
            return "Due tomorrow", "soon"
        if days == 0:
            return "Due today", "soon"
        return f"Overdue by {-days} day{'s' if days < -1 else ''}", "overdue"

    @app.get("/")
    def index():
        members = db.scalars(select(Member).order_by(Member.member_id)).all()
        return render_template("index.html", members=members)

    @app.get("/members/<member_id>")
    def member_page(member_id):
        member = db.get(Member, member_id) or abort(404)
        today = date.today()
        return render_template(
            "member.html",
            member=member,
            ducks=available_ducks(db),
            today=today,
            due_date_for=due_date_for,
        )

    @app.post("/members/<member_id>/loans")
    def borrow(member_id):
        try:
            loan = borrow_duck(db, member_id, request.form.get("duck_id", ""))
        except LoanError as e:
            flash(str(e), "error")
        else:
            message = (f"Loan {loan.loan_id} approved. Duck {loan.duck_id} is due back on "
                       f"{format_date(loan.due_date)}.")
            if loan.deposit_held:
                message += (f" A deposit of {format_money(loan.deposit_held)} is held "
                            "and will be refunded when you return it.")
            flash(message, "success")
        return redirect(url_for("member_page", member_id=member_id))

    @app.post("/members/<member_id>/loans/<loan_id>/return")
    def return_loan(member_id, loan_id):
        try:
            loan = return_duck(db, member_id, loan_id)
        except LoanError as e:
            flash(str(e), "error")
        else:
            message = f"Duck {loan.duck_id} returned. Thank you!"
            if loan.deposit_held:
                message += f" Your {format_money(loan.deposit_held)} deposit has been refunded."
            flash(message, "success")
        return redirect(url_for("member_page", member_id=member_id))

    return app


def seed_data(session) -> None:
    today = date.today()
    session.add_all([
        Member(member_id="M001", name="Alex Tan"),
        Member(member_id="M002", name="Sam Lim"),
        Member(member_id="M003", name="Priya Nair"),
        *[StandardDuck(duck_id=f"D{n:03d}") for n in range(1, 7)],
        *[DeluxeDuck(duck_id=f"X{n:03d}") for n in range(1, 4)],
    ])
    # M001 already has a duck out (so the "borrow another" case is ready to try)
    # and one past loan that has been returned; M002 has an overdue loan;
    # M003 has a Deluxe out with its deposit held.
    session.add_all([
        Loan(loan_id="L0001", member_id="M001", duck_id="D003",
             borrow_date=today - timedelta(days=40), due_date=today - timedelta(days=33),
             return_date=today - timedelta(days=35)),
        Loan(loan_id="L0002", member_id="M001", duck_id="D001",
             borrow_date=today - timedelta(days=3), due_date=today + timedelta(days=4)),
        Loan(loan_id="L0003", member_id="M002", duck_id="D002",
             borrow_date=today - timedelta(days=13), due_date=today - timedelta(days=6)),
        Loan(loan_id="L0004", member_id="M003", duck_id="X001",
             borrow_date=today - timedelta(days=2), due_date=today + timedelta(days=12),
             deposit_held=DeluxeDuck.DEFAULT_DEPOSIT),
    ])
    session.commit()


if __name__ == "__main__":
    create_app().run(debug=True)
