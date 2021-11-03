import typing
from abc import ABCMeta, abstractmethod


class QueueClientException(Exception):
    pass


class QueueDoesNotExistException(QueueClientException):
    def __init__(self, queue_name: str):
        super(QueueDoesNotExistException, self).__init__()
        self.queue_name = queue_name

    def __repr__(self):
        return f"QueueDoesNotExistException {self.queue_name}"


class QueueClient(object, metaclass=ABCMeta):
    @abstractmethod
    def add_message(self, queue_name: str, msg: str, delay: int):
        pass

    @abstractmethod
    def get_queues_by_prefixes(self, prefixes: typing.List[str]):
        pass

    @abstractmethod
    def get_queues_by_names(self, queue_names: typing.List[str]):
        pass
