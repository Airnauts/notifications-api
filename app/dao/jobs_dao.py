from sqlalchemy import desc, cast, Date as sql_date
from app import db
from app.dao import days_ago
from app.models import Job, NotificationHistory
from app.statsd_decorators import statsd
from sqlalchemy import func, asc


@statsd(namespace="dao")
def dao_get_notification_outcomes_for_job(service_id, job_id):
    query = db.session.query(
        func.count(NotificationHistory.status).label('count'),
        NotificationHistory.status.label('status')
    )

    return query \
        .filter(NotificationHistory.service_id == service_id) \
        .filter(NotificationHistory.job_id == job_id)\
        .group_by(NotificationHistory.status) \
        .order_by(asc(NotificationHistory.status)) \
        .all()


def dao_get_job_by_service_id_and_job_id(service_id, job_id):
    return Job.query.filter_by(service_id=service_id, id=job_id).one()


def dao_get_jobs_by_service_id(service_id, limit_days=None):
    query_filter = [Job.service_id == service_id]
    if limit_days is not None:
        query_filter.append(cast(Job.created_at, sql_date) >= days_ago(limit_days))
    return Job.query.filter(*query_filter).order_by(desc(Job.created_at)).all()


def dao_get_job_by_id(job_id):
    return Job.query.filter_by(id=job_id).one()


def dao_create_job(job):
    db.session.add(job)
    db.session.commit()


def dao_update_job(job):
    db.session.add(job)
    db.session.commit()
