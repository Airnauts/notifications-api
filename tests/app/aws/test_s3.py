from unittest.mock import call
from datetime import datetime, timedelta

from flask import current_app

from freezegun import freeze_time
import pytz

from app.aws.s3 import (
    get_s3_bucket_objects,
    get_s3_file,
    filter_s3_bucket_objects_within_date_range,
    remove_transformed_dvla_file
)


def datetime_in_past(days=0, seconds=0):
    return datetime.now(tz=pytz.utc) - timedelta(days=days, seconds=seconds)


def single_s3_object_stub(key='foo', last_modified=datetime.utcnow()):
    return {
        'ETag': '"d41d8cd98f00b204e9800998ecf8427e"',
        'Key': key,
        'LastModified': last_modified
    }


def test_get_s3_file_makes_correct_call(notify_api, mocker):
    get_s3_mock = mocker.patch('app.aws.s3.get_s3_object')
    get_s3_file('foo-bucket', 'bar-file.txt')

    get_s3_mock.assert_called_with(
        'foo-bucket',
        'bar-file.txt'
    )


def test_remove_transformed_dvla_file_makes_correct_call(notify_api, mocker):
    s3_mock = mocker.patch('app.aws.s3.get_s3_object')
    fake_uuid = '5fbf9799-6b9b-4dbb-9a4e-74a939f3bb49'

    remove_transformed_dvla_file(fake_uuid)

    s3_mock.assert_has_calls([
        call(current_app.config['DVLA_UPLOAD_BUCKET_NAME'], '{}-dvla-job.text'.format(fake_uuid)),
        call().delete()
    ])


def test_get_s3_bucket_objects_make_correct_pagination_call(notify_api, mocker):
    paginator_mock = mocker.patch('app.aws.s3.client')

    get_s3_bucket_objects('foo-bucket', subfolder='bar')

    paginator_mock.assert_has_calls([
        call().get_paginator().paginate(Bucket='foo-bucket', Prefix='bar')
    ])


def test_get_s3_bucket_objects_builds_objects_list_from_paginator(notify_api, mocker):
    paginator_mock = mocker.patch('app.aws.s3.client')
    multiple_pages_s3_object = [
        {
            "Contents": [
                single_s3_object_stub('bar/foo.txt', datetime_in_past(days=8)),
            ]
        },
        {
            "Contents": [
                single_s3_object_stub('bar/foo1.txt', datetime_in_past(days=8)),
            ]
        }
    ]
    paginator_mock.return_value.get_paginator.return_value.paginate.return_value = multiple_pages_s3_object

    bucket_objects = get_s3_bucket_objects('foo-bucket', subfolder='bar')

    assert len(bucket_objects) == 2
    assert set(bucket_objects[0].keys()) == set(['ETag', 'Key', 'LastModified'])


@freeze_time("2016-01-01 11:00:00")
def test_get_s3_bucket_objects_removes_redundant_root_object(notify_api, mocker):
    s3_objects_stub = [
        single_s3_object_stub('bar/', datetime_in_past(days=8)),
        single_s3_object_stub('bar/foo.txt', datetime_in_past(days=8)),
    ]

    filtered_items = filter_s3_bucket_objects_within_date_range(s3_objects_stub)

    assert len(filtered_items) == 1

    assert filtered_items[0]["Key"] == 'bar/foo.txt'
    assert filtered_items[0]["LastModified"] == datetime_in_past(days=8)


@freeze_time("2016-01-01 11:00:00")
def test_filter_s3_bucket_objects_within_date_range_filters_by_date_range(notify_api, mocker):
    s3_objects_stub = [
        single_s3_object_stub('bar/', datetime_in_past(days=8)),
        single_s3_object_stub('bar/foo.txt', datetime_in_past(days=8)),
        single_s3_object_stub('bar/foo1.txt', datetime_in_past(days=8)),
    ]

    filtered_items = filter_s3_bucket_objects_within_date_range(s3_objects_stub)

    assert len(filtered_items) == 2

    assert filtered_items[0]["Key"] == 'bar/foo.txt'
    assert filtered_items[0]["LastModified"] == datetime_in_past(days=8)

    assert filtered_items[1]["Key"] == 'bar/foo1.txt'
    assert filtered_items[1]["LastModified"] == datetime_in_past(days=8)


@freeze_time("2016-01-01 11:00:00")
def test_get_s3_bucket_objects_does_not_return_outside_of_date_range(notify_api, mocker):
    s3_objects_stub = [
        single_s3_object_stub('bar/', datetime_in_past(days=7)),
        single_s3_object_stub('bar/foo.txt', datetime_in_past(days=7)),
        single_s3_object_stub('bar/foo2.txt', datetime_in_past(days=9)),
        single_s3_object_stub('bar/foo2.txt', datetime_in_past(days=9, seconds=1)),
    ]

    filtered_items = filter_s3_bucket_objects_within_date_range(s3_objects_stub)

    assert len(filtered_items) == 0
