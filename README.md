# Rubber-Duck Lending Library (prototype)

Flask + SQLAlchemy + in-memory SQLite, with server-rendered Jinja templates.
The data resets every time the server restarts.

## Run

```
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000, pick a member, and borrow a duck.

Tests: `python -m unittest`

## What it covers

User story: *As a member, I want to borrow a duck from the library.*

| Acceptance criterion | Where |
|---|---|
| I can see when my duck is due back | Confirmation message after borrowing, plus the **Due back** / **Status** columns on the member page. Loans last 14 days (`LOAN_PERIOD` in `services.py`). |
| With an active loan, borrowing another duck is approved | `borrow_duck` in `services.py` has no limit on how many loans a member can have. Seeded member **M001** already has a duck out, so you can try it straight away. |

Assumption not stated in the story: a duck that is already on loan can't be borrowed until it has been returned.

## Layout

- `models.py`: `Member`, `Duck`, `Loan`, following the class diagram
- `services.py`: borrowing rules
- `app.py`: Flask routes and seed data
- `templates/`: HTML pages
- `test_app.py`: acceptance tests

Returning a duck is out of scope for this story. `Loan.return_date` exists and is shown in the page, but only the seed data sets it.
