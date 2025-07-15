import pytest
from uuid import uuid4
from unittest.mock import AsyncMock
from datetime import datetime

from app.crud import reports
from app.models.reports import CustomerReport, ProductReport
from app import exceptions


@pytest.mark.asyncio
async def test_customer_summary_success(monkeypatch, async_client, auth_headers):
    dummy = CustomerReport(
        total_spent=123.45,
        unique_products=3,
        last_transaction=datetime.now()
    )

    monkeypatch.setattr(reports, "get_customer_summary", AsyncMock(return_value=dummy))

    cid = str(uuid4())
    resp = await async_client.get(f"/reports/customer-summary/{cid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()['total_spent'] == dummy.total_spent
    assert resp.json()['unique_products'] == dummy.unique_products


@pytest.mark.asyncio
async def test_customer_summary_missing(monkeypatch, async_client, auth_headers):
    monkeypatch.setattr(reports, "get_customer_summary", AsyncMock(return_value=None))
    cid = str(uuid4())
    resp = await async_client.get(f"/reports/customer-summary/{cid}", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == exceptions.MISSING_CUSTOMER.detail


@pytest.mark.asyncio
async def test_product_summary_success(monkeypatch, async_client, auth_headers):
    dummy = ProductReport(
        total_revenue_pln=999.99,
        total_quantity=10,
        unique_customers=8
    )
    monkeypatch.setattr(reports, "get_product_summary", AsyncMock(return_value=dummy))

    pid = str(uuid4())
    resp = await async_client.get(f"/reports/product-summary/{pid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()['total_revenue_pln'] == dummy.total_revenue_pln
    assert resp.json()['total_quantity'] == dummy.total_quantity
    assert resp.json()['unique_customers'] == dummy.unique_customers


@pytest.mark.asyncio
async def test_product_summary_missing(monkeypatch, async_client, auth_headers):
    monkeypatch.setattr(reports, "get_product_summary", AsyncMock(return_value=None))
    pid = str(uuid4())
    resp = await async_client.get(f"/reports/product-summary/{pid}", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == exceptions.MISSING_PRODUCT.detail
