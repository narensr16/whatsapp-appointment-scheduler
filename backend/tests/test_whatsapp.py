"""Tests for WhatsApp Webhook endpoint and workflows."""
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from fastapi import status
from app.config import settings
from app.services.whatsapp_provider import MetaWhatsAppCloudProvider, get_whatsapp_provider


def test_meta_webhook_verification(client):
    """Test Meta webhook verification handshake."""
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": settings.META_VERIFY_TOKEN,
        "hub.challenge": "1158201444"
    }
    response = client.get("/whatsapp/", params=params)
    assert response.status_code == status.HTTP_200_OK
    assert response.text == "1158201444"


def test_meta_webhook_verification_bad_token(client):
    """Test Meta webhook rejection when token does not match."""
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "1158201444"
    }
    response = client.get("/whatsapp/", params=params)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_whatsapp_booking_success(client):
    """Test successful booking via mock WhatsApp webhook payload."""
    payload = {
        "sender": "+14155552671",
        "text": "Book appointment with Dr. A tomorrow at 10 AM",
        "message_id": "test_msg_001"
    }
    response = client.post("/whatsapp/", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "success"
    assert "confirmed" in data["reply"].lower()
    assert data["appointment"] is not None
    assert data["appointment"]["user_phone"] == "+14155552671"
    assert data["appointment"]["doctor_name"] == "Dr. Alice Smith"


def test_whatsapp_booking_ambiguous_message(client):
    """Test incomplete message returns clarification request."""
    payload = {
        "sender": "+14155552671",
        "text": "Book Dr. A",
        "message_id": "test_msg_ambiguous"
    }
    response = client.post("/whatsapp/", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "clarification_needed"
    assert "time" in data["reply"].lower() or "date" in data["reply"].lower()
    assert data["appointment"] is None


def test_whatsapp_booking_unknown_doctor(client):
    """Test message referencing unknown doctor prompts clarification with available roster."""
    payload = {
        "sender": "+14155552671",
        "text": "Book Dr. NonExistent tomorrow at 10 AM",
        "message_id": "test_msg_unknown_doc"
    }
    response = client.post("/whatsapp/", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "clarification_needed"
    assert "available doctors" in data["reply"].lower()


def test_whatsapp_booking_conflict_with_alternatives(client):
    """Test booking a booked slot returns conflict and suggested alternative slots."""
    # First booking via mock webhook
    p1 = {
        "sender": "+14155550001",
        "text": "Book Dr. B tomorrow at 2 PM",
        "message_id": "test_msg_b1"
    }
    res1 = client.post("/whatsapp/", json=p1)
    assert res1.status_code == status.HTTP_200_OK
    assert res1.json()["status"] == "success"

    # Second booking for the exact same slot
    p2 = {
        "sender": "+14155550002",
        "text": "Book Dr. B tomorrow at 2 PM",
        "message_id": "test_msg_b2"
    }
    res2 = client.post("/whatsapp/", json=p2)
    assert res2.status_code == status.HTTP_200_OK
    data2 = res2.json()
    assert data2["status"] == "conflict"
    assert "already booked" in data2["reply"].lower()
    assert data2["suggested_slots"] is not None
    assert len(data2["suggested_slots"]) > 0


def test_whatsapp_idempotency_duplicate_webhook(client):
    """Test repeated webhook delivery with same message_id returns cached reply and does not re-book."""
    payload = {
        "sender": "+14155557777",
        "text": "Book Dr. A tomorrow at 11 AM",
        "message_id": "idempotent_msg_100"
    }
    # Initial delivery
    res1 = client.post("/whatsapp/", json=payload)
    assert res1.status_code == status.HTTP_200_OK
    assert res1.json()["status"] == "success"

    # Duplicate delivery with identical message_id
    res2 = client.post("/whatsapp/", json=payload)
    assert res2.status_code == status.HTTP_200_OK
    data2 = res2.json()
    assert data2["status"] == "duplicate"


def test_meta_cloud_api_format_payload(client):
    """Test receiving real Meta WhatsApp Cloud API JSON structure."""
    meta_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550555",
                                "phone_number_id": "123456789"
                            },
                            "messages": [
                                {
                                    "from": "14155553333",
                                    "id": "wamid.HBgLMTQxNTU1NTMzMzM=",
                                    "timestamp": "1710000000",
                                    "text": {
                                        "body": "Book Dr. A tomorrow at 3 PM"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }

    response = client.post("/whatsapp/", json=meta_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "success"
    assert data["appointment"]["user_phone"] == "14155553333"


def test_meta_signature_verification_valid_and_invalid(client, monkeypatch):
    """Test HMAC-SHA256 signature verification when META_APP_SECRET is set."""
    test_secret = "test_meta_app_secret_12345"
    monkeypatch.setattr(settings, "META_APP_SECRET", test_secret)
    monkeypatch.setattr(settings, "WHATSAPP_PROVIDER", "meta")

    payload = {"sender": "+14155559876", "text": "Book Dr. A tomorrow at 10 AM", "message_id": "msg_sig_test"}
    body_bytes = json.dumps(payload).encode("utf-8")

    # 1. Invalid signature should be rejected with 401
    bad_headers = {"X-Hub-Signature-256": "sha256=invalidhashvalue000000"}
    res_bad = client.post("/whatsapp/", content=body_bytes, headers={"Content-Type": "application/json", **bad_headers})
    assert res_bad.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. Valid signature should be accepted with 200 OK
    valid_hash = hmac.new(key=test_secret.encode("utf-8"), msg=body_bytes, digestmod=hashlib.sha256).hexdigest()
    good_headers = {"X-Hub-Signature-256": f"sha256={valid_hash}"}
    res_good = client.post("/whatsapp/", content=body_bytes, headers={"Content-Type": "application/json", **good_headers})
    assert res_good.status_code == status.HTTP_200_OK


def test_meta_delivery_status_event_handling(client):
    """Test delivery status event payload from Meta is gracefully processed."""
    status_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "15550555", "phone_number_id": "123456789"},
                            "statuses": [
                                {
                                    "id": "wamid.HBgLMTQxNTU1NTMzMzM=",
                                    "status": "delivered",
                                    "timestamp": "1710000100",
                                    "recipient_id": "14155553333"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    response = client.post("/whatsapp/", json=status_payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "status_update"


def test_meta_malformed_and_empty_payloads(client):
    """Test malformed and empty webhook payloads are handled without server errors."""
    res_empty = client.post("/whatsapp/", json={})
    assert res_empty.status_code == status.HTTP_200_OK
    assert res_empty.json()["status"] == "ignored"

    res_empty_entry = client.post("/whatsapp/", json={"entry": []})
    assert res_empty_entry.status_code == status.HTTP_200_OK
    assert res_empty_entry.json()["status"] == "ignored"


def test_outbound_meta_provider_failure_reporting():
    """Verify that MetaWhatsAppCloudProvider safely reports error when credentials are not configured."""
    provider = MetaWhatsAppCloudProvider()
    res = provider.send_message("+14155551234", "Test message")
    assert res["provider"] == "meta"
    assert res["delivered"] is False
    assert "error" in res


def test_whatsapp_booking_twilio_from_body_payload(client):
    """Test regression: Twilio/Mock style From and Body payload is recognized and booked."""
    payload = {
        "From": "+14155552671",
        "Body": "Book appointment with Dr. A at 10 AM tomorrow"
    }
    response = client.post("/whatsapp/", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "success"
    assert "confirmed" in data["reply"].lower()
    assert data["appointment"] is not None
    assert data["appointment"]["user_phone"] == "+14155552671"
    assert data["appointment"]["doctor_name"] == "Dr. Alice Smith"
    assert data["message_id"] is not None


def test_whatsapp_booking_meta_nested_payload_regression(client):
    """Test regression: Meta WhatsApp Cloud API nested payload continues to be processed properly."""
    meta_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550555",
                                "phone_number_id": "123456789"
                            },
                            "messages": [
                                {
                                    "from": "+14155554444",
                                    "id": "wamid.regression_meta_001",
                                    "timestamp": "1710000200",
                                    "text": {
                                        "body": "Book Dr. B tomorrow at 4 PM"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    response = client.post("/whatsapp/", json=meta_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "success"
    assert data["appointment"] is not None
    assert data["appointment"]["user_phone"] == "+14155554444"
    assert data["appointment"]["doctor_name"] == "Dr. Bob Jones"
    assert data["message_id"] == "wamid.regression_meta_001"


def test_cors_preflight_for_frontend_ports(client):
    """Test CORS preflight allows common frontend origins including fallback port 5174."""
    for origin in ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5174"]:
        headers = {
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
        res = client.options("/whatsapp/", headers=headers)
        assert res.status_code == status.HTTP_200_OK
        assert res.headers.get("access-control-allow-origin") == origin

    # Verify disallowed origin is rejected
    disallowed_headers = {
        "Origin": "http://evil-site.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    res_disallowed = client.options("/whatsapp/", headers=disallowed_headers)
    assert res_disallowed.status_code == status.HTTP_400_BAD_REQUEST
    assert "access-control-allow-origin" not in res_disallowed.headers



