from datetime import date, timedelta


def _days_ago(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    product TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    payment_method TEXT NOT NULL,
    fulfillment_status TEXT NOT NULL,
    ordered_on TEXT NOT NULL,
    street TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    country TEXT NOT NULL DEFAULT 'US'
);

CREATE TABLE IF NOT EXISTS credit_applications (
    customer_id TEXT PRIMARY KEY REFERENCES customers(customer_id),
    application_id TEXT NOT NULL,
    status TEXT NOT NULL,
    full_name TEXT NOT NULL,
    ssn_last4 TEXT NOT NULL,
    id_document_type TEXT NOT NULL,
    annual_income REAL NOT NULL,
    requested_limit REAL NOT NULL
);
"""

SEED_CUSTOMERS = (
    ("cust_201", "Elena Vasquez", "555-0198", "elena.vasquez@example.com"),
    ("cust_193", "James Okonkwo", "555-0142", "james.okonkwo@example.com"),
    ("cust_118", "Maya Chen", "555-0170", "maya.chen@example.com"),
    ("cust_169", "Nora Patel", "555-0169", "nora.patel@example.com"),
)

SEED_ORDERS = (
    (
        "ORD-1488",
        "cust_201",
        "Table lamp",
        80,
        "USD",
        "card",
        "processing",
        _days_ago(2),
        "44 Cedar Ave",
        "Portland",
        "OR",
        "97205",
        "US",
    ),
    (
        "ORD-1501",
        "cust_193",
        "Coffee maker",
        150,
        "USD",
        "card",
        "processing",
        _days_ago(4),
        "7 Oak St",
        "Portland",
        "OR",
        "97209",
        "US",
    ),
    (
        "ORD-1704",
        "cust_118",
        "Oak dining chairs (set of 2)",
        240,
        "USD",
        "card",
        "processing",
        _days_ago(1),
        "12 Pine Rd",
        "Portland",
        "OR",
        "97202",
        "US",
    ),
    (
        "ORD-1690",
        "cust_169",
        "Sectional sofa",
        800,
        "USD",
        "card",
        "dispatched",
        _days_ago(6),
        "91 River Dr",
        "Portland",
        "OR",
        "97211",
        "US",
    ),
    (
        "ORD-1602",
        "cust_201",
        "Linen throw",
        45,
        "USD",
        "card",
        "delivered",
        _days_ago(12),
        "44 Cedar Ave",
        "Portland",
        "OR",
        "97205",
        "US",
    ),
    (
        "ORD-1618",
        "cust_118",
        "Ceramic vase",
        55,
        "USD",
        "card",
        "delivered",
        _days_ago(20),
        "12 Pine Rd",
        "Portland",
        "OR",
        "97202",
        "US",
    ),
)

SEED_CREDIT_APPLICATIONS = (
    (
        "cust_193",
        "cred_193",
        "under_review",
        "James Okonkwo",
        "4412",
        "drivers_license",
        62000,
        1500,
    ),
)
