from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ..models.models import CreditApplication, Customer, Order, ShippingAddress
from .schema import SCHEMA, SEED_CREDIT_APPLICATIONS, SEED_CUSTOMERS, SEED_ORDERS

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "maplewood.db"

_db_path: Path | None = None


def db_path() -> Path:
    if _db_path is not None:
        return _db_path
    env_path = os.environ.get("MAPLEWOOD_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def set_db_path(path: str | Path) -> None:
    global _db_path
    _db_path = Path(path)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        _init(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def reset(path: str | Path | None = None) -> None:
    if path is not None:
        set_db_path(path)
    target = db_path()
    for candidate in (target, Path(f"{target}-wal"), Path(f"{target}-shm")):
        if candidate.exists():
            candidate.unlink()
    with connect():
        pass


def get_customer_by_phone(phone: str) -> Customer | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT customer_id, name, phone, email FROM customers WHERE phone = ?",
            (phone,),
        ).fetchone()
        if row is None:
            return None
        return _customer_from_row(conn, row)


def get_order(order_id: str | None) -> Order | None:
    if not order_id:
        return None
    with connect() as conn:
        return _order_from_id(conn, order_id)


def get_credit_application(customer_id: str) -> CreditApplication | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT customer_id, application_id, status, full_name, ssn_last4,
                   id_document_type, annual_income, requested_limit
            FROM credit_applications
            WHERE customer_id = ?
            """,
            (customer_id,),
        ).fetchone()
        if row is None:
            return None
        return CreditApplication(**dict(row))


def customer_count() -> int:
    with connect() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM customers").fetchone()["n"]


def update_order_amount(order_id: str, amount: float) -> Order | None:
    with connect() as conn:
        cursor = conn.execute(
            "UPDATE orders SET amount = ? WHERE order_id = ?",
            (amount, order_id),
        )
        if cursor.rowcount == 0:
            return None
        return _order_from_id(conn, order_id)


def update_order_shipping_address(order_id: str, address: ShippingAddress) -> Order | None:
    with connect() as conn:
        cursor = conn.execute(
            """
            UPDATE orders
            SET street = ?, city = ?, state = ?, postal_code = ?, country = ?
            WHERE order_id = ?
            """,
            (
                address.street,
                address.city,
                address.state,
                address.postal_code,
                address.country,
                order_id,
            ),
        )
        if cursor.rowcount == 0:
            return None
        return _order_from_id(conn, order_id)


def update_order_fulfillment_status(order_id: str, fulfillment_status: str) -> Order | None:
    with connect() as conn:
        cursor = conn.execute(
            "UPDATE orders SET fulfillment_status = ? WHERE order_id = ?",
            (fulfillment_status, order_id),
        )
        if cursor.rowcount == 0:
            return None
        return _order_from_id(conn, order_id)


def _init(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    if conn.execute("SELECT COUNT(*) AS n FROM customers").fetchone()["n"] == 0:
        _seed(conn)


def _seed(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT INTO customers (customer_id, name, phone, email) VALUES (?, ?, ?, ?)",
        SEED_CUSTOMERS,
    )
    conn.executemany(
        """
        INSERT INTO orders (
            order_id, customer_id, product, amount, currency, payment_method,
            fulfillment_status, street, city, state, postal_code, country
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        SEED_ORDERS,
    )
    conn.executemany(
        """
        INSERT INTO credit_applications (
            customer_id, application_id, status, full_name, ssn_last4,
            id_document_type, annual_income, requested_limit
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        SEED_CREDIT_APPLICATIONS,
    )


def _customer_from_row(conn: sqlite3.Connection, row: sqlite3.Row) -> Customer:
    order_ids = [
        item["order_id"]
        for item in conn.execute(
            "SELECT order_id FROM orders WHERE customer_id = ? ORDER BY order_id",
            (row["customer_id"],),
        ).fetchall()
    ]
    return Customer(
        customer_id=row["customer_id"],
        name=row["name"],
        phone=row["phone"],
        email=row["email"],
        order_ids=order_ids,
    )


def _order_from_id(conn: sqlite3.Connection, order_id: str) -> Order | None:
    row = conn.execute(
        """
        SELECT order_id, customer_id, product, amount, currency, payment_method,
               fulfillment_status, street, city, state, postal_code, country
        FROM orders
        WHERE order_id = ?
        """,
        (order_id,),
    ).fetchone()
    if row is None:
        return None
    return Order(
        order_id=row["order_id"],
        customer_id=row["customer_id"],
        product=row["product"],
        amount=row["amount"],
        currency=row["currency"],
        payment_method=row["payment_method"],
        fulfillment_status=row["fulfillment_status"],
        shipping_address=ShippingAddress(
            street=row["street"],
            city=row["city"],
            state=row["state"],
            postal_code=row["postal_code"],
            country=row["country"],
        ),
    )
