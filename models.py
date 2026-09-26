"""Domain model, mirroring the class diagram:
Member 1--0..* Loan 0..*--1 Duck, where Duck is a StandardDuck or a DeluxeDuck."""
from datetime import date
from typing import ClassVar

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Member(Base):
    __tablename__ = "member"

    member_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)

    loans: Mapped[list["Loan"]] = relationship(
        back_populates="member", order_by="Loan.borrow_date.desc()"
    )


class Duck(Base):
    """Abstract: every duck is either a StandardDuck or a DeluxeDuck (single table)."""
    __tablename__ = "duck"
    __mapper_args__ = {"polymorphic_on": "kind", "polymorphic_abstract": True}

    DEFAULT_LOAN_PERIOD_DAYS: ClassVar[int]

    duck_id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String)
    loan_period_days: Mapped[int] = mapped_column(Integer)

    loans: Mapped[list["Loan"]] = relationship(back_populates="duck")

    def __init__(self, **kwargs):
        kwargs.setdefault("loan_period_days", self.DEFAULT_LOAN_PERIOD_DAYS)
        super().__init__(**kwargs)

    @property
    def label(self) -> str:
        return self.kind.capitalize()

    @property
    def required_deposit(self) -> float:
        """Deposit taken when this duck is borrowed."""
        return 0.0

    @property
    def current_loan(self) -> "Loan | None":
        return next((loan for loan in self.loans if loan.is_active), None)


class StandardDuck(Duck):
    __mapper_args__ = {"polymorphic_identity": "standard"}

    DEFAULT_LOAN_PERIOD_DAYS = 7


class DeluxeDuck(Duck):
    """Bigger, squeakier, more motivational. Kept longer, but needs a deposit."""
    __mapper_args__ = {"polymorphic_identity": "deluxe"}

    DEFAULT_LOAN_PERIOD_DAYS = 14
    DEFAULT_DEPOSIT = 5.00

    # Nullable because standard ducks share the table and have no deposit.
    deposit_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __init__(self, **kwargs):
        kwargs.setdefault("deposit_amount", self.DEFAULT_DEPOSIT)
        super().__init__(**kwargs)

    @property
    def required_deposit(self) -> float:
        return self.deposit_amount


class Loan(Base):
    __tablename__ = "loan"

    loan_id: Mapped[str] = mapped_column(String, primary_key=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("member.member_id"))
    duck_id: Mapped[str] = mapped_column(ForeignKey("duck.duck_id"))
    borrow_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Amount taken when the loan was made; refunded in full when the duck is returned.
    deposit_held: Mapped[float] = mapped_column(Float, default=0.0)

    member: Mapped[Member] = relationship(back_populates="loans")
    duck: Mapped[Duck] = relationship(back_populates="loans")

    @property
    def is_active(self) -> bool:
        return self.return_date is None
