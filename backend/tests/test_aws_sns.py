import pytest
from unittest.mock import MagicMock, patch
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

def test_send_sms_simulation_fallback():
    # Calling without active credentials should fall back to simulation mode gracefully
    res = aws_sns_service.send_sms_otp("+91 98220 12345", "123456", custom_credentials=None)
    assert res["success"] is True
    assert res["mode"] == "simulation"
    assert res["phone"] == "+919822012345"
    assert "SIM-SNS" in res["message_id"]
    assert res["simulated"] is True

def test_send_sms_with_mocked_boto3():
    fake_creds = {
        "aws_access_key_id": "AKIA_FAKE_TEST_KEY_123",
        "aws_secret_access_key": "SECRET_FAKE_KEY_XYZ",
        "region_name": "ap-south-1"
    }
    
    mock_boto_client = MagicMock()
    mock_boto_client.publish.return_value = {
        "MessageId": "aws-msg-999-alpha-test",
        "ResponseMetadata": {"HTTPStatusCode": 200}
    }
    
    with patch("boto3.client", return_value=mock_boto_client) as mock_boto:
        res = aws_sns_service.send_sms_otp(
            phone_number="78880 85822",
            otp_code="654321",
            custom_credentials=fake_creds
        )
        
        assert res["success"] is True
        assert res["mode"] == "aws_sns"
        assert res["message_id"] == "aws-msg-999-alpha-test"
        assert res["phone"] == "+917888085822"
        assert res["simulated"] is False
        
        # Verify boto3 publish call arguments
        mock_boto_client.publish.assert_called_once()
        call_kwargs = mock_boto_client.publish.call_args[1]
        assert call_kwargs["PhoneNumber"] == "+917888085822"
        assert "654321" in call_kwargs["Message"]
        assert call_kwargs["MessageAttributes"]["AWS.SNS.SMS.SMSType"]["StringValue"] == "Transactional"

def test_generate_login_otp_dispatches_with_aws_metadata():
    rec = generate_login_otp("+91 98231 55555")
    assert rec["channel"] == "SMS"
    assert "dispatch_mode" in rec
    assert "aws_message_id" in rec
    assert "aws_status_text" in rec
    assert "is_simulated" in rec
    assert rec["region"] == "ap-south-1"
