import typing

from django.conf import settings

from eb_sqs.worker.worker_factory import WorkerFactory

AWS_REGION: str = getattr(settings, "EB_AWS_REGION", "us-east-1")

MAX_NUMBER_OF_MESSAGES: int = getattr(settings, "EB_SQS_MAX_NUMBER_OF_MESSAGES", 10)
WAIT_TIME_S: int = getattr(settings, "EB_SQS_WAIT_TIME_S", 2)
NO_QUEUES_WAIT_TIME_S: int = getattr(settings, "NO_QUEUES_WAIT_TIME_S", 5)

AUTO_ADD_QUEUE: bool = getattr(settings, "EB_SQS_AUTO_ADD_QUEUE", False)
QUEUE_PREFIX: str = getattr(settings, "EB_SQS_QUEUE_PREFIX", "")
DEFAULT_QUEUE: str = getattr(settings, "EB_SQS_DEFAULT_QUEUE", "eb-sqs-default")

EXECUTE_INLINE: bool = getattr(settings, "EB_SQS_EXECUTE_INLINE", False)
FORCE_SERIALIZATION: bool = getattr(settings, "EB_SQS_FORCE_SERIALIZATION", False)

DEFAULT_DELAY: int = getattr(settings, "EB_SQS_DEFAULT_DELAY", 0)
DEFAULT_MAX_RETRIES: int = getattr(settings, "EB_SQS_DEFAULT_MAX_RETRIES", 0)
DEFAULT_COUNT_RETRIES: bool = getattr(settings, "EB_SQS_DEFAULT_COUNT_RETRIES", True)

USE_PICKLE: bool = getattr(settings, "EB_SQS_USE_PICKLE", False)

# TODO: change to use importlib
WORKER_FACTORY: typing.Union[str, WorkerFactory] = getattr(
    settings, "EB_SQS_WORKER_FACTORY", None
)

# importable queue client class definition
QUEUE_CLIENT_CLASS: str = getattr(
    settings, "EB_SQS_QUEUE_CLIENT_CLASS", "eb_sqs.aws.sqs_queue_client.SqsQueueClient"
)

DEAD_LETTER_MODE: bool = getattr(settings, "EB_SQS_DEAD_LETTER_MODE", False)

AWS_MAX_RETRIES: int = getattr(settings, "EB_SQS_AWS_MAX_RETRIES", 30)

REFRESH_PREFIX_QUEUES_S: int = getattr(settings, "EB_SQS_REFRESH_PREFIX_QUEUES_S", 10)

QUEUE_MESSAGE_RETENTION: str = getattr(
    settings, "EB_SQS_QUEUE_MESSAGE_RETENTION", "1209600"
)
QUEUE_VISIBILITY_TIMEOUT: str = getattr(
    settings, "EB_SQS_QUEUE_VISIBILITY_TIMEOUT", "300"
)

MIN_HEALTHCHECK_WRITE_PERIOD_S: int = getattr(
    settings, "EB_SQS_MIN_HEALTHCHECK_WRITE_PERIOD_S", 10
)
HEALTHCHECK_UNHEALTHY_PERIOD_S: int = getattr(
    settings, "EB_SQS_HEALTHCHECK_UNHEALTHY_PERIOD_S", int(QUEUE_VISIBILITY_TIMEOUT)
)
HEALTHCHECK_FILE_NAME: str = getattr(
    settings, "EB_SQS_HEALTHCHECK_FILE_NAME", "healthcheck.txt"
)
