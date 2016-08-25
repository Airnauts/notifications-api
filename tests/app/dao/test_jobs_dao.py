from datetime import (datetime, timedelta)
import uuid

from app.dao.jobs_dao import (
    dao_get_job_by_service_id_and_job_id,
    dao_create_job,
    dao_update_job,
    dao_get_jobs_by_service_id,
    dao_get_notification_outcomes_for_job)

from app.models import Job
from tests.app.conftest import sample_notification, sample_job, sample_service


def test_should_have_decorated_notifications_dao_functions():
    assert dao_get_notification_outcomes_for_job.__wrapped__.__name__ == 'dao_get_notification_outcomes_for_job'  # noqa


def test_should_get_all_statuses_for_notifications_associated_with_job(
        notify_db,
        notify_db_session,
        sample_service,
        sample_job):

    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='created')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='sending')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='delivered')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='pending')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='failed')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='technical-failure')  # noqa
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='temporary-failure')  # noqa
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='permanent-failure')  # noqa

    results = dao_get_notification_outcomes_for_job(sample_service.id, sample_job.id)
    assert [(row.count, row.status) for row in results] == [
        (1, 'created'),
        (1, 'sending'),
        (1, 'delivered'),
        (1, 'pending'),
        (1, 'failed'),
        (1, 'technical-failure'),
        (1, 'temporary-failure'),
        (1, 'permanent-failure')
    ]


def test_should_count_of_statuses_for_notifications_associated_with_job(
        notify_db,
        notify_db_session,
        sample_service,
        sample_job):
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='created')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='created')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='sending')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='sending')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='sending')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='sending')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='delivered')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=sample_job, status='delivered')

    results = dao_get_notification_outcomes_for_job(sample_service.id, sample_job.id)
    assert [(row.count, row.status) for row in results] == [
        (2, 'created'),
        (4, 'sending'),
        (2, 'delivered')
    ]


def test_should_return_zero_length_array_if_no_notifications_for_job(sample_service, sample_job):
    assert len(dao_get_notification_outcomes_for_job(sample_job.id, sample_service.id)) == 0


def test_should_return_notifications_only_for_this_job(notify_db, notify_db_session, sample_service):
    job_1 = sample_job(notify_db, notify_db_session, service=sample_service)
    job_2 = sample_job(notify_db, notify_db_session, service=sample_service)

    sample_notification(notify_db, notify_db_session, service=sample_service, job=job_1, status='created')
    sample_notification(notify_db, notify_db_session, service=sample_service, job=job_2, status='created')

    results = dao_get_notification_outcomes_for_job(sample_service.id, job_1.id)
    assert [(row.count, row.status) for row in results] == [
        (1, 'created')
    ]


def test_should_return_notifications_only_for_this_service(notify_db, notify_db_session):
    service_1 = sample_service(notify_db, notify_db_session, service_name="one", email_from="one")
    service_2 = sample_service(notify_db, notify_db_session, service_name="two", email_from="two")

    job_1 = sample_job(notify_db, notify_db_session, service=service_1)
    job_2 = sample_job(notify_db, notify_db_session, service=service_2)

    sample_notification(notify_db, notify_db_session, service=service_1, job=job_1, status='created')
    sample_notification(notify_db, notify_db_session, service=service_2, job=job_2, status='created')

    assert len(dao_get_notification_outcomes_for_job(service_1.id, job_2.id)) == 0


def test_create_job(sample_template):
    assert Job.query.count() == 0

    job_id = uuid.uuid4()
    data = {
        'id': job_id,
        'service_id': sample_template.service.id,
        'template_id': sample_template.id,
        'template_version': sample_template.version,
        'original_file_name': 'some.csv',
        'notification_count': 1,
        'created_by': sample_template.created_by
    }

    job = Job(**data)
    dao_create_job(job)

    assert Job.query.count() == 1
    job_from_db = Job.query.get(job_id)
    assert job == job_from_db
    assert job_from_db.notifications_delivered == 0
    assert job_from_db.notifications_failed == 0


def test_get_job_by_id(sample_job):
    job_from_db = dao_get_job_by_service_id_and_job_id(sample_job.service.id, sample_job.id)
    assert sample_job == job_from_db


def test_get_jobs_for_service(notify_db, notify_db_session, sample_template):
    from tests.app.conftest import sample_job as create_job
    from tests.app.conftest import sample_service as create_service
    from tests.app.conftest import sample_template as create_template
    from tests.app.conftest import sample_user as create_user

    one_job = create_job(notify_db, notify_db_session, sample_template.service, sample_template)

    other_user = create_user(notify_db, notify_db_session, email="test@digital.cabinet-office.gov.uk")
    other_service = create_service(notify_db, notify_db_session, user=other_user, service_name="other service",
                                   email_from='other.service')
    other_template = create_template(notify_db, notify_db_session, service=other_service)
    other_job = create_job(notify_db, notify_db_session, service=other_service, template=other_template)

    one_job_from_db = dao_get_jobs_by_service_id(one_job.service_id)
    other_job_from_db = dao_get_jobs_by_service_id(other_job.service_id)

    assert len(one_job_from_db) == 1
    assert one_job == one_job_from_db[0]

    assert len(other_job_from_db) == 1
    assert other_job == other_job_from_db[0]

    assert one_job_from_db != other_job_from_db


def test_get_jobs_for_service_with_limit_days_param(notify_db, notify_db_session, sample_template):
    from tests.app.conftest import sample_job as create_job

    one_job = create_job(notify_db, notify_db_session, sample_template.service, sample_template)
    old_job = create_job(notify_db, notify_db_session, sample_template.service, sample_template,
                         created_at=datetime.now() - timedelta(days=8))

    jobs = dao_get_jobs_by_service_id(one_job.service_id)

    assert len(jobs) == 2
    assert one_job in jobs
    assert old_job in jobs

    jobs_limit_days = dao_get_jobs_by_service_id(one_job.service_id, limit_days=7)
    assert len(jobs_limit_days) == 1
    assert one_job in jobs_limit_days
    assert old_job not in jobs_limit_days


def test_get_jobs_for_service_with_limit_days_edge_case(notify_db, notify_db_session, sample_template):
    from tests.app.conftest import sample_job as create_job

    one_job = create_job(notify_db, notify_db_session, sample_template.service, sample_template)
    job_two = create_job(notify_db, notify_db_session, sample_template.service, sample_template,
                         created_at=(datetime.now() - timedelta(days=7)).date())
    one_second_after_midnight = datetime.combine((datetime.now() - timedelta(days=7)).date(),
                                                 datetime.strptime("000001", "%H%M%S").time())
    just_after_midnight_job = create_job(notify_db, notify_db_session, sample_template.service, sample_template,
                                         created_at=one_second_after_midnight)
    job_eight_days_old = create_job(notify_db, notify_db_session, sample_template.service, sample_template,
                                    created_at=datetime.now() - timedelta(days=8))

    jobs_limit_days = dao_get_jobs_by_service_id(one_job.service_id, limit_days=7)
    assert len(jobs_limit_days) == 3
    assert one_job in jobs_limit_days
    assert job_two in jobs_limit_days
    assert just_after_midnight_job in jobs_limit_days
    assert job_eight_days_old not in jobs_limit_days


def test_get_jobs_for_service_in_created_at_order(notify_db, notify_db_session, sample_template):
    from tests.app.conftest import sample_job as create_job

    job_1 = create_job(
        notify_db, notify_db_session, sample_template.service, sample_template, created_at=datetime.utcnow())
    job_2 = create_job(
        notify_db, notify_db_session, sample_template.service, sample_template, created_at=datetime.utcnow())
    job_3 = create_job(
        notify_db, notify_db_session, sample_template.service, sample_template, created_at=datetime.utcnow())
    job_4 = create_job(
        notify_db, notify_db_session, sample_template.service, sample_template, created_at=datetime.utcnow())

    jobs = dao_get_jobs_by_service_id(sample_template.service.id)

    assert len(jobs) == 4
    assert jobs[0].id == job_4.id
    assert jobs[1].id == job_3.id
    assert jobs[2].id == job_2.id
    assert jobs[3].id == job_1.id


def test_update_job(sample_job):
    assert sample_job.status == 'pending'

    sample_job.status = 'in progress'

    dao_update_job(sample_job)

    job_from_db = Job.query.get(sample_job.id)

    assert job_from_db.status == 'in progress'
