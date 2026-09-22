from .models.models import Customer, Order, ShippingAddress


CUSTOMERS: dict[str, Customer] = {
    "555-0198": Customer(
        customer_id="cust_201",
        name="Elena Vasquez",
        phone="555-0198",
        email="elena.vasquez@example.com",
        order_ids=["ORD-1488"],
    ),
    "555-0142": Customer(
        customer_id="cust_193",
        name="James Okonkwo",
        phone="555-0142",
        email="james.okonkwo@example.com",
        order_ids=["ORD-1501"],
    ),
    "555-0170": Customer(
        customer_id="cust_118",
        name="Maya Chen",
        phone="555-0170",
        email="maya.chen@example.com",
        order_ids=["ORD-1704"],
    ),
    "555-0169": Customer(
        customer_id="cust_169",
        name="Nora Patel",
        phone="555-0169",
        email="nora.patel@example.com",
        order_ids=["ORD-1690"],
    ),
}

ORDERS: dict[str, Order] = {
    "ORD-1488": Order(
        order_id="ORD-1488",
        customer_id="cust_201",
        product="Table lamp",
        amount=80,
        payment_method="card",
        fulfillment_status="processing",
        shipping_address=ShippingAddress(
            street="44 Cedar Ave", city="Portland", state="OR", postal_code="97205"
        ),
    ),
    "ORD-1501": Order(
        order_id="ORD-1501",
        customer_id="cust_193",
        product="Coffee maker",
        amount=150,
        payment_method="card",
        fulfillment_status="processing",
        shipping_address=ShippingAddress(
            street="7 Oak St", city="Portland", state="OR", postal_code="97209"
        ),
    ),
    "ORD-1704": Order(
        order_id="ORD-1704",
        customer_id="cust_118",
        product="Oak dining chairs (set of 2)",
        amount=240,
        payment_method="card",
        fulfillment_status="processing",
        shipping_address=ShippingAddress(
            street="12 Pine Rd", city="Portland", state="OR", postal_code="97202"
        ),
    ),
    "ORD-1690": Order(
        order_id="ORD-1690",
        customer_id="cust_169",
        product="Sectional sofa",
        amount=800,
        payment_method="card",
        fulfillment_status="dispatched",
        shipping_address=ShippingAddress(
            street="91 River Dr", city="Portland", state="OR", postal_code="97211"
        ),
    ),
}

CREDIT_APPLICATIONS = {
    "cust_193": {
        "application_id": "cred_193",
        "status": "under_review",
        "full_name": "James Okonkwo",
        "ssn_last4": "4412",
        "id_document_type": "drivers_license",
        "annual_income": 62000,
        "requested_limit": 1500,
    }
}
