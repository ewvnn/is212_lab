"""Domain model, mirroring the class diagram: Member 1--0..* Loan 0..*--1 Duck."""
from datetime import date

from sqlalchemy import Date, ForeignKey, String
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
    __tablename__ = "duck"

    duck_id: Mapped[str] = mapped_column(String, primary_key=True)

    loans: Mapped[list["Loan"]] = relationship(back_populates="duck")

    @property
    def current_loan(self) -> "Loan | None":
        return next((loan for loan in self.loans if loan.is_active), None)


class Loan(Base):
    __tablename__ = "loan"

    loan_id: Mapped[str] = mapped_column(String, primary_key=True)
    member_id: Mapped[str] = mapped_column(ForeignKey("member.member_id"))
    duck_id: Mapped[str] = mapped_column(ForeignKey("duck.duck_id"))
    borrow_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    member: Mapped[Member] = relationship(back_populates="loans")
    duck: Mapped[Duck] = relationship(back_populates="loans")

    @property
    def is_active(self) -> bool:
        return self.return_date is None
