from __future__ import absolute_import, unicode_literals

from eb_sqs.aws.sqs_queue_client import SqsQueueClient
from eb_sqs.worker.worker import Worker
from eb_sqs.worker.worker_factory import WorkerFactory


class SqsWorkerFactory(WorkerFactory):
    _WORKER = None  # type: Worker

    def __init__(self):
        super(SqsWorkerFactory, self).__init__()

    def create(self):
        if not SqsWorkerFactory._WORKER:
            # TODO: add setting so we can specify the queue client class
            queue_client = SqsQueueClient()
            SqsWorkerFactory._WORKER = Worker(queue_client)
        return SqsWorkerFactory._WORKER
