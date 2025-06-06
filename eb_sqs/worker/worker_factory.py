from abc import ABCMeta, abstractmethod

from eb_sqs import settings
from eb_sqs.worker.worker import Worker


class WorkerFactory(object, metaclass=ABCMeta):
    def __init__(self):
        super(WorkerFactory, self).__init__()

    @abstractmethod
    def create(self) -> Worker:
        pass

    @staticmethod
    def default() -> "WorkerFactory":
        if not settings.WORKER_FACTORY:
            from eb_sqs.worker.sqs_worker_factory import SqsWorkerFactory

            return SqsWorkerFactory()
        else:
            return settings.WORKER_FACTORY
