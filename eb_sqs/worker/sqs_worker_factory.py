from __future__ import absolute_import, unicode_literals

from django.utils.module_loading import import_string

from eb_sqs import settings
from eb_sqs.worker.worker import Worker
from eb_sqs.worker.worker_factory import WorkerFactory


class SqsWorkerFactory(WorkerFactory):
    _WORKER = None  # type: Worker

    def __init__(self):
        super(SqsWorkerFactory, self).__init__()

    def create(self):
        if not SqsWorkerFactory._WORKER:
            queue_client_class = import_string(settings.QUEUE_CLIENT_CLASS)
            queue_client = queue_client_class()
            SqsWorkerFactory._WORKER = Worker(queue_client)
        return SqsWorkerFactory._WORKER
