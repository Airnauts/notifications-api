from datetime import datetime, timedelta
import json

from freezegun import freeze_time

from app import db
from app.models import TemplateStatistics
from tests import create_authorization_header
from tests.app.conftest import sample_template as create_sample_template, sample_template, sample_notification, \
    sample_email_template


def test_get_all_template_statistics_with_bad_arg_returns_400(notify_api, sample_service):
    with notify_api.test_request_context():
        with notify_api.test_client() as client:

            auth_header = create_authorization_header()

            response = client.get(
                '/service/{}/template-statistics'.format(sample_service.id),
                headers=[('Content-Type', 'application/json'), auth_header],
                query_string={'limit_days': 'blurk'}
            )

            assert response.status_code == 400
            json_resp = json.loads(response.get_data(as_text=True))
            assert json_resp['result'] == 'error'
            assert json_resp['message'] == {'limit_days': ['blurk is not an integer']}


@freeze_time('2016-08-18')
def test_get_template_statistics_for_service(notify_db, notify_db_session, notify_api, sample_service):
    sms = sample_template(notify_db, notify_db_session, service=sample_service)
    email = sample_email_template(notify_db, notify_db_session, service=sample_service)
    today = datetime.now()
    sample_notification(notify_db, notify_db_session, created_at=today, service=sample_service, template=sms)
    sample_notification(notify_db, notify_db_session, created_at=today, service=sample_service, template=sms)
    sample_notification(notify_db, notify_db_session, created_at=today, service=sample_service, template=email)
    sample_notification(notify_db, notify_db_session, created_at=today, service=sample_service, template=email)

    with notify_api.test_request_context():
        with notify_api.test_client() as client:

            auth_header = create_authorization_header()

            response = client.get(
                '/service/{}/template-statistics'.format(sample_service.id),
                headers=[('Content-Type', 'application/json'), auth_header]
            )

            assert response.status_code == 200
            json_resp = json.loads(response.get_data(as_text=True))
            assert len(json_resp['data']) == 2
            assert json_resp['data'][0]['count'] == 2
            assert json_resp['data'][0]['template_id'] == str(email.id)
            assert json_resp['data'][0]['template_name'] == email.name
            assert json_resp['data'][0]['template_type'] == email.template_type
            assert json_resp['data'][1]['count'] == 2
            assert json_resp['data'][1]['template_id'] == str(sms.id)
            assert json_resp['data'][1]['template_name'] == sms.name
            assert json_resp['data'][1]['template_type'] == sms.template_type


@freeze_time('2016-08-18')
def test_get_template_statistics_for_service_limited_by_day(notify_db, notify_db_session, notify_api, sample_service):
    sms = sample_template(notify_db, notify_db_session, service=sample_service)
    email = sample_email_template(notify_db, notify_db_session, service=sample_service)
    today = datetime.now()
    a_week_ago = datetime.now() - timedelta(days=7)
    a_month_ago = datetime.now() - timedelta(days=30)
    sample_notification(notify_db, notify_db_session, created_at=today, service=sample_service, template=sms)
    sample_notification(notify_db, notify_db_session, created_at=today, service=sample_service, template=email)
    sample_notification(notify_db, notify_db_session, created_at=a_week_ago, service=sample_service, template=sms)
    sample_notification(notify_db, notify_db_session, created_at=a_week_ago, service=sample_service, template=email)
    sample_notification(notify_db, notify_db_session, created_at=a_month_ago, service=sample_service, template=sms)
    sample_notification(notify_db, notify_db_session, created_at=a_month_ago, service=sample_service, template=email)

    with notify_api.test_request_context():
        with notify_api.test_client() as client:

            auth_header = create_authorization_header()

            response = client.get(
                '/service/{}/template-statistics'.format(sample_service.id),
                headers=[('Content-Type', 'application/json'), auth_header],
                query_string={'limit_days': 1}
            )

            assert response.status_code == 200
            json_resp = json.loads(response.get_data(as_text=True))
            assert len(json_resp['data']) == 2
            assert json_resp['data'][0]['count'] == 1
            assert json_resp['data'][0]['template_id'] == str(email.id)
            assert json_resp['data'][0]['template_name'] == email.name
            assert json_resp['data'][0]['template_type'] == email.template_type
            assert json_resp['data'][1]['count'] == 1
            assert json_resp['data'][1]['template_id'] == str(sms.id)
            assert json_resp['data'][1]['template_name'] == sms.name
            assert json_resp['data'][1]['template_type'] == sms.template_type

            response_for_a_week = client.get(
                '/service/{}/template-statistics'.format(sample_service.id),
                headers=[('Content-Type', 'application/json'), auth_header],
                query_string={'limit_days': 7}
            )

            assert response.status_code == 200
            json_resp = json.loads(response_for_a_week.get_data(as_text=True))
            assert len(json_resp['data']) == 2
            assert json_resp['data'][0]['count'] == 2
            assert json_resp['data'][0]['template_name'] == 'Email Template Name'
            assert json_resp['data'][1]['count'] == 2
            assert json_resp['data'][1]['template_name'] == 'Template Name'

            response_for_a_month = client.get(
                '/service/{}/template-statistics'.format(sample_service.id),
                headers=[('Content-Type', 'application/json'), auth_header],
                query_string={'limit_days': 30}
            )

            assert response_for_a_month.status_code == 200
            json_resp = json.loads(response_for_a_month.get_data(as_text=True))
            assert len(json_resp['data']) == 2
            assert json_resp['data'][0]['count'] == 3
            assert json_resp['data'][0]['template_name'] == 'Email Template Name'
            assert json_resp['data'][1]['count'] == 3
            assert json_resp['data'][1]['template_name'] == 'Template Name'

            response_for_all = client.get(
                '/service/{}/template-statistics'.format(sample_service.id),
                headers=[('Content-Type', 'application/json'), auth_header]
            )

            assert response_for_all.status_code == 200
            json_resp = json.loads(response_for_all.get_data(as_text=True))
            assert len(json_resp['data']) == 2
            assert json_resp['data'][0]['count'] == 3
            assert json_resp['data'][0]['template_name'] == 'Email Template Name'
            assert json_resp['data'][1]['count'] == 3
            assert json_resp['data'][1]['template_name'] == 'Template Name'


@freeze_time('2016-08-18')
def test_returns_empty_list_if_no_templates_used(notify_api, sample_service):
    with notify_api.test_request_context():
        with notify_api.test_client() as client:

            auth_header = create_authorization_header()

            response = client.get(
                '/service/{}/template-statistics'.format(sample_service.id),
                headers=[('Content-Type', 'application/json'), auth_header]
            )

            assert response.status_code == 200
            json_resp = json.loads(response.get_data(as_text=True))
            assert len(json_resp['data']) == 0


def test_get_template_statistics_for_template_only_returns_for_provided_template(
        notify_db,
        notify_db_session,
        notify_api,
        sample_service
):
    template_1 = create_sample_template(
        notify_db,
        notify_db_session,
        template_name='Sample Template 1',
        service=sample_service
    )
    template_2 = create_sample_template(
        notify_db,
        notify_db_session,
        template_name='Sample Template 2',
        service=sample_service
    )

    template_1_stats_1 = TemplateStatistics(
        template_id=template_1.id,
        service_id=sample_service.id,
        day=datetime(2001, 1, 1)
    )
    template_1_stats_2 = TemplateStatistics(
        template_id=template_1.id,
        service_id=sample_service.id,
        day=datetime(2001, 1, 2)
    )
    template_2_stats = TemplateStatistics(
        template_id=template_2.id,
        service_id=sample_service.id,
        day=datetime(2001, 1, 1)
    )

    # separate commit to ensure stats_1 has earlier updated_at time
    db.session.add(template_1_stats_1)
    db.session.commit()

    db.session.add_all([template_1_stats_2, template_2_stats])
    db.session.commit()

    with notify_api.test_request_context():
        with notify_api.test_client() as client:
            auth_header = create_authorization_header()

            response = client.get(
                '/service/{}/template-statistics/{}'.format(sample_service.id, template_1.id),
                headers=[('Content-Type', 'application/json'), auth_header],
            )

            assert response.status_code == 200
            json_resp = json.loads(response.get_data(as_text=True))
            assert len(json_resp['data']) == 2
            assert json_resp['data'][0]['id'] == str(template_1_stats_2.id)
            assert json_resp['data'][1]['id'] == str(template_1_stats_1.id)


def test_get_template_statistics_for_template_returns_empty_if_no_statistics(
        notify_db,
        notify_db_session,
        notify_api,
        sample_service
):
    template_1 = create_sample_template(
        notify_db,
        notify_db_session,
        template_name='Sample Template 1',
        service=sample_service
    )
    template_2 = create_sample_template(
        notify_db,
        notify_db_session,
        template_name='Sample Template 2',
        service=sample_service
    )

    template_1_stats = TemplateStatistics(
        template_id=template_1.id,
        service_id=sample_service.id,
        day=datetime(2001, 1, 1)
    )
    db.session.add(template_1_stats)
    db.session.commit()

    with notify_api.test_request_context():
        with notify_api.test_client() as client:
            auth_header = create_authorization_header()

            response = client.get(
                '/service/{}/template-statistics/{}'.format(sample_service.id, template_2.id),
                headers=[('Content-Type', 'application/json'), auth_header],
            )

            assert response.status_code == 200
            json_resp = json.loads(response.get_data(as_text=True))
            assert json_resp['data'] == []
