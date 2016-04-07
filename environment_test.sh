#!/bin/bash
export NOTIFY_API_ENVIRONMENT='config.Test'
export ADMIN_BASE_URL='http://localhost:6012'
export ADMIN_CLIENT_USER_NAME='dev-notify-admin'
export ADMIN_CLIENT_SECRET='dev-notify-secret-key'
export AWS_REGION='eu-west-1'
export DANGEROUS_SALT='dangerous-salt'
export INVITATION_EMAIL_FROM='invites'
export INVITATION_EXPIRATION_DAYS=2
export NOTIFY_JOB_QUEUE='notify-jobs-queue-test'
export NOTIFICATION_QUEUE_PREFIX='notification_development-test'
export SECRET_KEY='secret-key'
export SQLALCHEMY_DATABASE_URI='postgresql://localhost/test_notification_api'
export VERIFY_CODE_FROM_EMAIL_ADDRESS='no-reply@notify.works'
export TWILIO_ACCOUNT_SID="test"
export TWILIO_AUTH_TOKEN="test"
export TWILIO_NUMBER="test"
export FIRETEXT_API_KEY="Firetext"
export FIRETEXT_NUMBER="Firetext"
export NOTIFY_EMAIL_DOMAIN="test.notify.com"
export MMG_API_KEY='mmg-secret-key'
export MMG_FROM_NUMBER='test'