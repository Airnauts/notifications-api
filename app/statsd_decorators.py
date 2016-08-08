import functools

from app import statsd_client
from flask import current_app
from monotonic import monotonic


def statsd(namespace):
    def time_function(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = monotonic()
            res = func(*args, **kwargs)
            elapsed_time = monotonic() - start_time
            current_app.logger.info(
                "{namespace} call {func} took {time}".format(
                    namespace=namespace, func=func.__name__, time="{0:.4f}".format(elapsed_time)
                )
            )
            statsd_client.incr('{namespace}.{func}'.format(
                namespace=namespace, func=func.__name__)
            )
            statsd_client.timing('{namespace}.{func}'.format(
                namespace=namespace, func=func.__name__), elapsed_time
            )
            return res
        wrapper.__wrapped__.__name__ = func.__name__
        return wrapper

    return time_function
