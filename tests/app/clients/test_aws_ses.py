import botocore
import pytest
from unittest.mock import Mock, ANY
from notifications_utils.recipients import InvalidEmailError

from app import aws_ses_client
from app.clients.email.aws_ses import get_aws_responses, AwsSesClientException, AwsSesClientThrottlingSendRateException


def test_should_return_correct_details_for_delivery():
    response_dict = get_aws_responses('Delivery')
    assert response_dict['message'] == 'Delivered'
    assert response_dict['notification_status'] == 'delivered'
    assert response_dict['notification_statistics_status'] == 'delivered'
    assert response_dict['success']


def test_should_return_correct_details_for_hard_bounced():
    response_dict = get_aws_responses('Permanent')
    assert response_dict['message'] == 'Hard bounced'
    assert response_dict['notification_status'] == 'permanent-failure'
    assert response_dict['notification_statistics_status'] == 'failure'
    assert not response_dict['success']


def test_should_return_correct_details_for_soft_bounced():
    response_dict = get_aws_responses('Temporary')
    assert response_dict['message'] == 'Soft bounced'
    assert response_dict['notification_status'] == 'temporary-failure'
    assert response_dict['notification_statistics_status'] == 'failure'
    assert not response_dict['success']


def test_should_return_correct_details_for_complaint():
    response_dict = get_aws_responses('Complaint')
    assert response_dict['message'] == 'Complaint'
    assert response_dict['notification_status'] == 'delivered'
    assert response_dict['notification_statistics_status'] == 'delivered'
    assert response_dict['success']


def test_should_be_none_if_unrecognised_status_code():
    with pytest.raises(KeyError) as e:
        get_aws_responses('99')
    assert '99' in str(e.value)


@pytest.mark.parametrize('reply_to_address, expected_value', [
    (None, []),
    ('foo@bar.com', ['foo@bar.com']),
    ('føøøø@bååååår.com', ['føøøø@xn--br-yiaaaaa.com'])
], ids=['empty', 'single_email', 'punycode'])
def test_send_email_handles_reply_to_address(notify_api, mocker, reply_to_address, expected_value):
    boto_mock = mocker.patch.object(aws_ses_client, '_client', create=True)
    mocker.patch.object(aws_ses_client, 'statsd_client', create=True)

    with notify_api.app_context():
        aws_ses_client.send_email(
            source=Mock(),
            to_addresses='to@address.com',
            subject=Mock(),
            body=Mock(),
            reply_to_address=reply_to_address
        )

    boto_mock.send_email.assert_called_once_with(
        Source=ANY,
        Destination=ANY,
        Message=ANY,
        ReplyToAddresses=expected_value
    )


def test_send_email_handles_punycode_to_address(notify_api, mocker):
    boto_mock = mocker.patch.object(aws_ses_client, '_client', create=True)
    mocker.patch.object(aws_ses_client, 'statsd_client', create=True)

    with notify_api.app_context():
        aws_ses_client.send_email(
            Mock(),
            to_addresses='føøøø@bååååår.com',
            subject=Mock(),
            body=Mock()
        )

    boto_mock.send_email.assert_called_once_with(
        Source=ANY,
        Destination={'ToAddresses': ['føøøø@xn--br-yiaaaaa.com'], 'CcAddresses': [], 'BccAddresses': []},
        Message=ANY,
        ReplyToAddresses=ANY
    )


def test_send_email_raises_bad_email_as_InvalidEmailError(mocker):
    boto_mock = mocker.patch.object(aws_ses_client, '_client', create=True)
    mocker.patch.object(aws_ses_client, 'statsd_client', create=True)
    error_response = {
        'Error': {
            'Code': 'InvalidParameterValue',
            'Message': 'some error message from amazon',
            'Type': 'Sender'
        }
    }
    boto_mock.send_email.side_effect = botocore.exceptions.ClientError(error_response, 'opname')
    mocker.patch.object(aws_ses_client, 'statsd_client', create=True)

    with pytest.raises(InvalidEmailError) as excinfo:
        aws_ses_client.send_email(
            source=Mock(),
            to_addresses='definitely@invalid_email.com',
            subject=Mock(),
            body=Mock()
        )

    assert 'some error message from amazon' in str(excinfo.value)
    assert 'definitely@invalid_email.com' in str(excinfo.value)


def test_send_email_raises_send_rate_throttling_as_AwsSesClientThrottlingSendRateException(mocker):
    boto_mock = mocker.patch.object(aws_ses_client, '_client', create=True)
    mocker.patch.object(aws_ses_client, 'statsd_client', create=True)
    error_response = {
        'Error': {
            'Code': 'Throttling',
            'Message': 'Maximum sending rate exceeded.',
            'Type': 'Sender'
        }
    }
    boto_mock.send_email.side_effect = botocore.exceptions.ClientError(error_response, 'opname')

    with pytest.raises(AwsSesClientThrottlingSendRateException):
        aws_ses_client.send_email(
            source=Mock(),
            to_addresses='foo@bar.com',
            subject=Mock(),
            body=Mock()
        )


def test_send_email_does_not_raise_AwsSesClientThrottlingSendRateException_if_non_send_rate_throttling(mocker):
    boto_mock = mocker.patch.object(aws_ses_client, '_client', create=True)
    mocker.patch.object(aws_ses_client, 'statsd_client', create=True)
    error_response = {
        'Error': {
            'Code': 'Throttling',
            'Message': 'Daily message quota exceeded',
            'Type': 'Sender'
        }
    }
    boto_mock.send_email.side_effect = botocore.exceptions.ClientError(error_response, 'opname')

    with pytest.raises(AwsSesClientException):
        aws_ses_client.send_email(
            source=Mock(),
            to_addresses='foo@bar.com',
            subject=Mock(),
            body=Mock()
        )


def test_send_email_raises_other_errs_as_AwsSesClientException(mocker):
    boto_mock = mocker.patch.object(aws_ses_client, '_client', create=True)
    mocker.patch.object(aws_ses_client, 'statsd_client', create=True)
    error_response = {
        'Error': {
            'Code': 'ServiceUnavailable',
            'Message': 'some error message from amazon',
            'Type': 'Sender'
        }
    }
    boto_mock.send_email.side_effect = botocore.exceptions.ClientError(error_response, 'opname')
    mocker.patch.object(aws_ses_client, 'statsd_client', create=True)

    with pytest.raises(AwsSesClientException) as excinfo:
        aws_ses_client.send_email(
            source=Mock(),
            to_addresses='foo@bar.com',
            subject=Mock(),
            body=Mock()
        )

    assert 'some error message from amazon' in str(excinfo.value)
