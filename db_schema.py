import datetime
import decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    DECIMAL
)
from sqlalchemy.orm import (
    relationship,
    mapped_column,
    Mapped
)
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.current_timestamp()
    )


class Wallet(BaseModel):
    __tablename__ = 'wallet'

    label: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[decimal.Decimal] = mapped_column(DECIMAL(precision=18, scale=2), default=0)

    transactions = relationship('Transaction', back_populates='wallet')


class Transaction(BaseModel):
    __tablename__ = 'transaction'

    wallet_id: Mapped[int] = mapped_column(Integer, ForeignKey('wallet.id'))
    txid: Mapped[str] = mapped_column(String(36))
    amount: Mapped[decimal.Decimal] = mapped_column(DECIMAL(precision=18, scale=2))

    wallet = relationship('Wallet', back_populates='transactions')
