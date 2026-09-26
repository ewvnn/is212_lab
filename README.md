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

## Change request: Deluxe Duck

> We are introducing a premium Deluxe Duck — bigger, squeakier, more motivational.
> Members can keep a Deluxe for 14 days instead of 7, and because they are expensive,
> borrowing one requires a small returnable deposit. Standard ducks are unchanged.

In the model, `Duck` is now abstract, with two subclasses: `StandardDuck` (7 days) and `DeluxeDuck` (14 days, `depositAmount`, $5.00 by default). The loan period is stored on each duck as `loanPeriodDays`. Each loan records the deposit it took in `depositHeld`.

## User stories

Each story has its own test class in `test_app.py`.

### US1: As a member, I want to borrow a duck from the library. (`BorrowDuckTest`)

| Acceptance criterion | Where |
|---|---|
| I can see when my duck is due back | Confirmation message after borrowing, plus the **Due back** / **Status** columns on the member page. |
| With an active loan, borrowing another duck is approved | `borrow_duck` in `services.py` has no limit on how many loans a member can have. Seeded member **M001** already has a duck out. |

### US2: As a member, I want to borrow a Deluxe duck for 14 days, so that I can keep the extra motivation for longer. (`DeluxeLoanPeriodTest`)

| Acceptance criterion | Where |
|---|---|
| A Deluxe duck is due back 14 days after borrowing | `borrow_duck` uses the duck's `loan_period_days` (`due_date_for` in `services.py`). |
| A Standard duck is still due back after 7 days | `StandardDuck.DEFAULT_LOAN_PERIOD_DAYS` in `models.py`. |
| Before borrowing, I can see each duck's type and the date it would be due back | **Type** and **Due back if borrowed today** columns on the member page. |

### US3: As a member, I want to know the deposit for a Deluxe duck and see that it is held on my loan, so that I know what I am paying and that I will get it back. (`DeluxeDepositTest`)

| Acceptance criterion | Where |
|---|---|
| The deposit is shown before I borrow | **Deposit** column in the "Borrow a duck" table. |
| Borrowing a Deluxe duck holds its deposit | `Loan.deposit_held` is set from `duck.required_deposit`. It appears in the confirmation message and in the **Deposit** column of "My loans". |
| Standard ducks need no deposit | `Duck.required_deposit` is 0; only `DeluxeDuck` overrides it. |

### US4: As a member, I want to return a duck, so that my deposit is refunded and the duck is free for someone else. (`ReturnDuckTest`)

| Acceptance criterion | Where |
|---|---|
| I can return a duck I have on loan | **Return** button on "My loans" → `return_duck` in `services.py` sets `return_date`. |
| Returning a Deluxe duck refunds its deposit in full | The confirmation message says so, and the deposit shows as "refunded". Seeded member **M003** has a Deluxe out to try this. |
| A returned duck can be borrowed again | It reappears in "Borrow a duck". |
| I can't return a loan twice, or someone else's loan | `return_duck` raises `LoanError` and the page shows the error. |

## Assumptions

- A duck that is already on loan can't be borrowed until it has been returned.
- The deposit is $5.00 per Deluxe duck. The change request only says "small".
- The prototype has no payments. Taking and refunding the deposit is recorded on the loan, not charged.
- Returning an overdue duck is allowed, and there are no late fees.

## Layout

- `models.py`: `Member`, `Duck` (`StandardDuck`, `DeluxeDuck`), `Loan`, following the class diagram
- `services.py`: borrowing and return rules
- `app.py`: Flask routes and seed data
- `templates/`: HTML pages
- `test_app.py`: acceptance tests
