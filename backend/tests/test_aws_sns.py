import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from app.services.aws_sns import aws_sns_service, format_e164
from app.core.security import generate_login_otp, verify_login_otp

def test_format_e164_normalization():
    # 10-digit Indian numbers without country code
    assert format_e164("7888085822") == "+917888085822"
    assert format_e164("78880 85822") == "+917888085822"
    assert format_e164("09822012345") == "+919822012345"

    # 12-digit numbers starting with 91
    assert format_e164("917888085822") == "+917888085822"

    # Already formatted E.164 numbers
    assert format_e164("+91 78880 85822") == "+917888085822"
    assert format_e164("+1 555-123-4567") == "+15551234567"
    assert format_e164("+44 20 7946 0958") == "+442079460958"

def test_sns_configuration_inspector():
    config = aws_sns_service.check_sns_configuration()
    assert "boto3_available" in config
    assert config["boto3_available"] is True
    assert "region" in config
    assert "status" in config

def test_send_sms_without_credentials_reports_failure():
    # With no credentials anywhere, SMS must fail loudly instead of simulating
    with patch("boto3.Session.get_credentials", return_value=None):
        res = aws_sns_service.send_sms_otp("+91 98220 12345", "123456", custom_credentials=None)
    assert res["success"] is False
    assert res["mode"] == "not_configured"
    assert res["phone"] == "+919822012345"
    assert res["simulated"] is False
    assert "123456" not in str(res)

def test_send_sms_with_mocked_boto3():
    fake_creds = {
        "aws_access_key_id": "AKIA_FAKE_TEST_KEY_123",
        "aws_secret_access_key": "SECRET_FAKE_KEY_XYZ",
        "aws_session_token": "FAKE_SESSION_TOKEN",
        "region_name": "us-east-1"
    }

    mock_boto_client = MagicMock()
    mock_boto_client.publish.return_value = {
        "MessageId": "aws-msg-999-alpha-test",
        "ResponseMetadata": {"HTTPStatusCode": 200}
    }

    with patch("boto3.Session.client", return_value=mock_boto_client):
        res = aws_sns_service.send_sms_otp(
            phone_number="78880 85822",
            otp_code="654321",
            custom_credentials=fake_creds
        )

        assert res["success"] is True
        assert res["mode"] == "aws_sns"
        assert res["message_id"] == "aws-msg-999-alpha-test"
        assert res["phone"] == "+917888085822"
        assert res["region"] == "us-east-1"
        assert res["simulated"] is False

        # Verify boto3 publish call arguments
        mock_boto_client.publish.assert_called_once()
        call_kwargs = mock_boto_client.publish.call_args[1]
        assert call_kwargs["PhoneNumber"] == "+917888085822"
        assert "654321" in call_kwargs["Message"]
        assert call_kwargs["MessageAttributes"]["AWS.SNS.SMS.SMSType"]["StringValue"] == "Transactional"

def test_send_sms_includes_optional_dlt_attributes(monkeypatch):
    monkeypatch.setenv("SNS_SMS_SENDER_ID", "FAMFIO")
    monkeypatch.setenv("SNS_SMS_ENTITY_ID", "1101000000000000000")
    monkeypatch.setenv("SNS_SMS_TEMPLATE_ID", "1107000000000000000")
    fake_creds = {"aws_access_key_id": "AKIA_FAKE", "aws_secret_access_key": "SECRET_FAKE"}

    mock_boto_client = MagicMock()
    mock_boto_client.publish.return_value = {"MessageId": "aws-msg-dlt"}
    with patch("boto3.Session.client", return_value=mock_boto_client):
        res = aws_sns_service.send_sms_otp("78880 85822", "111222", custom_credentials=fake_creds)

    assert res["success"] is True
    attrs = mock_boto_client.publish.call_args[1]["MessageAttributes"]
    assert attrs["AWS.SNS.SMS.SenderID"]["StringValue"] == "FAMFIO"
    assert attrs["AWS.MM.SMS.EntityId"]["StringValue"] == "1101000000000000000"
    assert attrs["AWS.MM.SMS.TemplateId"]["StringValue"] == "1107000000000000000"

def test_send_sms_publish_error_reports_failure():
    fake_creds = {"aws_access_key_id": "AKIA_FAKE", "aws_secret_access_key": "SECRET_FAKE"}
    mock_boto_client = MagicMock()
    mock_boto_client.publish.side_effect = ClientError(
        {"Error": {"Code": "AuthorizationError", "Message": "Not authorized to publish"}}, "Publish"
    )
    with patch("boto3.Session.client", return_value=mock_boto_client):
        res = aws_sns_service.send_sms_otp("78880 85822", "333444", custom_credentials=fake_creds)

    assert res["success"] is False
    assert res["mode"] == "aws_sns_error"
    assert "Not authorized" in res["error"]
    assert "333444" not in str(res)

def test_generate_login_otp_not_stored_when_sms_fails():
    identifier = "+91 98231 55555"
    with patch("boto3.Session.get_credentials", return_value=None):
        rec = generate_login_otp(identifier)
    assert rec["channel"] == "SMS"
    assert rec["delivered"] is False
    assert rec["dispatch_error"]
    assert rec["dispatch_mode"] == "not_configured"
    # An undelivered OTP must not be usable for login
    is_valid, _ = verify_login_otp(identifier, rec["otp"])
    assert is_valid is False
