from abc import ABCMeta, abstractmethod


class QueueClientException(Exception):
    pass


class QueueDoesNotExistException(QueueClientException):
    def __init__(self, queue_name):
        # type: (unicode) -> None
        super(QueueDoesNotExistException, self).__init__()
        self.queue_name = queue_name


class QueueClient(object, metaclass=ABCMeta):
    @abstractmethod
    def add_message(self, queue_name, msg, delay):
        # type: (unicode, unicode, int) -> None
        pass

    @abstractmethod
    def get_queues_by_prefixes(self, prefixes):
        # type: (list) -> list
        pass

    @abstractmethod
    def get_queues_by_names(self, queue_names):
        # type: (list) -> list
        pass
