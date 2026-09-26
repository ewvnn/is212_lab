# AGENTS.md

Rubber-duck lending library prototype for IS212: Flask, SQLAlchemy 2.x, in-memory SQLite, and Jinja templates. See `README.md` for the user stories, their acceptance criteria and the Deluxe Duck change request.

## Commands

- Install: `pip install -r requirements.txt`
- Run: `python app.py` (serves http://127.0.0.1:5000; data resets on restart)
- Test: `python -m unittest`

## Layout

- `models.py`: `Member`, `Duck`, `Loan`. `Duck` is abstract, with subclasses `StandardDuck` and `DeluxeDuck` in one table. Keep these matching the class diagram (Member 1--0..* Loan 0..*--1 Duck).
- `services.py`: borrowing and return rules. Put business logic here, not in routes.
- `app.py`: `create_app(seed=...)`, the routes, and the seed data.
- `templates/`: server-rendered pages that extend `base.html`.
- `test_app.py`: acceptance tests, one class per user story.

## Rules

- A member may have any number of active loans. Don't add a cap.
- A duck that is already on loan can't be borrowed. `borrow_duck` raises `LoanError` in that case.
- A loan's due date comes from the duck's `loan_period_days`: 7 for Standard, 14 for Deluxe (`DEFAULT_LOAN_PERIOD_DAYS` on each subclass). Don't hardcode day counts anywhere else.
- Only Deluxe ducks take a deposit (`required_deposit`). `Loan.deposit_held` records it, and it is refunded in full when the duck is returned. There are no real payments.
- Put behaviour that differs by duck type on the `Duck` subclasses, not in `if kind == ...` checks.
- Tests build the app with `create_app(seed=False)` and add their own rows. Run `python -m unittest` before you finish a change.
- Keep changes small and in the existing style: type hints, SQLAlchemy 2.0 `Mapped`/`select` API, short docstrings.
- Don't commit `__pycache__/` or scratch files.
