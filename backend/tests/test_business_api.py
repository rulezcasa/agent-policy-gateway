from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_customer_lookup_and_order_detail() -> None:
    customer = client.get("/customers", params={"phone": "555-0198"})
    assert customer.status_code == 200
    assert customer.json()["customer_id"] == "cust_201"

    order = client.get("/orders/ORD-1488")
    assert order.status_code == 200
    assert order.json()["product"] == "Table lamp"


def test_refund_defaults_payment_method_from_order() -> None:
    response = client.post(
        "/orders/ORD-1501/refunds",
        json={
            "order_id": "ORD-1501",
            "customer_id": "cust_193",
            "amount": 150,
            "currency": "USD",
            "reason": "defective coffee maker",
        },
    )
    assert response.status_code == 200
    assert response.json()["payment_method"] == "card"


def test_discount_updates_order_total() -> None:
    response = client.post(
        "/orders/ORD-1488/discounts",
        json={
            "order_id": "ORD-1488",
            "discount_percent": 25,
            "reason": "sorry discount",
        },
    )
    assert response.status_code == 200
    assert response.json()["amount"] == 60


def test_customer_data_and_export_contracts() -> None:
    credit = client.get("/customers/cust_193/credit-application")
    assert credit.status_code == 200
    assert credit.json()["application_id"] == "cred_193"

    export = client.post(
        "/customers/export",
        json={"destination": "partner_campaign", "reason": "export list for partner"},
    )
    assert export.status_code == 200
    assert export.json()["customer_count"] == 4


def test_shipping_update_and_cancel() -> None:
    shipping = client.put(
        "/orders/ORD-1704/shipping-address",
        json={
            "street": "88 Harbor St",
            "city": "Portland",
            "state": "OR",
            "postal_code": "97201",
        },
    )
    assert shipping.status_code == 200
    assert shipping.json()["shipping_address"]["street"] == "88 Harbor St"

    cancelled = client.post(
        "/orders/ORD-1690/cancel",
        json={"order_id": "ORD-1690", "reason": "customer changed mind"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["fulfillment_status"] == "cancelled"
