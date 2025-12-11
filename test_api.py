import pytest
import requests
import uuid

BASE_URL = "http://localhost:5000"
API_KEY = "uqood-judge-access-key-2025"

def test_health_check():
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'
    except requests.exceptions.ConnectionError:
        pytest.fail("Server is not running. Please start the server before running tests.")

def test_create_contract_valid():
    payload = {
        "supplier": "شركة التقنية المتقدمة",
        "buyer": "مؤسسة الأفق التجارية",
        "items": "توريد 50 جهاز حاسب آلي محمول",
        "price": 150000
    }
    headers = {"X-API-Key": API_KEY}
    response = requests.post(f"{BASE_URL}/api/contract", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "supplier_url" in data
    assert "buyer_url" in data
    
    return data['id']  # Return ID for further tests if needed

def test_create_contract_invalid():
    payload = {
        "supplier": "", # Invalid (too short)
        "price": -100 # Invalid
    }
    headers = {"X-API-Key": API_KEY}
    response = requests.post(f"{BASE_URL}/api/contract", json=payload, headers=headers)
    assert response.status_code == 400
    assert "error" in response.json()

def test_create_contract_unauthorized():
    payload = {"supplier": "Test", "buyer": "Test", "items": "Test", "price": 100}
    response = requests.post(f"{BASE_URL}/api/contract", json=payload) # No API Key
    assert response.status_code == 401
