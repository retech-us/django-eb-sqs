import logging
import signal
import typing
from datetime import timedelta
from time import sleep

import django.dispatch
from botocore.exceptions import ClientError
from django.utils import timezone

from eb_sqs import settings
from eb_sqs.worker.commons import django_db_management
from eb_sqs.worker.queue_client import QueueClient
from eb_sqs.worker.worker import Worker
from eb_sqs.worker.worker_exceptions import ExecutionFailedException
from eb_sqs.worker.worker_factory import WorkerFactory

logger = logging.getLogger(__name__)

MESSAGES_RECEIVED = django.dispatch.Signal(providing_args=['messages'])
MESSAGES_PROCESSED = django.dispatch.Signal(providing_args=['messages'])
MESSAGES_DELETED = django.dispatch.Signal(providing_args=['messages'])


class WorkerService(object):
    _PREFIX_STR = 'prefix:'
    _RECEIVE_COUNT_ATTRIBUTE = 'ApproximateReceiveCount'

    def __init__(self, sqs_client: QueueClient):
        self._exit_gracefully = False
        self._last_healthcheck_time = None
        self.sqs_client = sqs_client

    def process_queues(self, queue_names: typing.List[str]):
        signal.signal(signal.SIGTERM, self._exit_called)

        self.write_healthcheck_file()
        self._last_healthcheck_time = timezone.now()

        logger.debug('[django-eb-sqs] Connecting to SQS: {}'.format(', '.join(queue_names)))

        prefixes = list([qn for qn in queue_names if qn.startswith(self._PREFIX_STR)])
        queues = self.sqs_client.get_queues_by_names(
            list(set(queue_names) - set(prefixes))
        )

        queue_prefixes = [prefix.split(self._PREFIX_STR)[1] for prefix in prefixes]
        static_queues = queues
        last_update_time = timezone.now() - timedelta(seconds=settings.REFRESH_PREFIX_QUEUES_S)

        logger.debug('[django-eb-sqs] Connected to SQS: {}'.format(', '.join(queue_names)))

        worker = WorkerFactory.default().create()

        logger.info('[django-eb-sqs] WAIT_TIME_S = {}'.format(settings.WAIT_TIME_S))
        logger.info('[django-eb-sqs] NO_QUEUES_WAIT_TIME_S = {}'.format(settings.NO_QUEUES_WAIT_TIME_S))
        logger.info('[django-eb-sqs] MAX_NUMBER_OF_MESSAGES = {}'.format(settings.MAX_NUMBER_OF_MESSAGES))
        logger.info('[django-eb-sqs] AUTO_ADD_QUEUE = {}'.format(settings.AUTO_ADD_QUEUE))
        logger.info('[django-eb-sqs] QUEUE_PREFIX = {}'.format(settings.QUEUE_PREFIX))
        logger.info('[django-eb-sqs] DEFAULT_QUEUE = {}'.format(settings.DEFAULT_QUEUE))
        logger.info('[django-eb-sqs] DEFAULT_MAX_RETRIES = {}'.format(settings.DEFAULT_MAX_RETRIES))
        logger.info('[django-eb-sqs] REFRESH_PREFIX_QUEUES_S = {}'.format(settings.REFRESH_PREFIX_QUEUES_S))

        while not self._exit_gracefully:
            if len(queue_prefixes) > 0 and \
                    timezone.now() - timedelta(seconds=settings.REFRESH_PREFIX_QUEUES_S) > last_update_time:
                queues = static_queues + self.sqs_client.get_queues_by_prefixes(queue_prefixes)
                last_update_time = timezone.now()
                logger.debug('[django-eb-sqs] Updated SQS queues: {}'.format(
                    ', '.join([queue.url for queue in queues])
                ))

            logger.debug('[django-eb-sqs] Processing {} queues'.format(len(queues)))
            if len(queues) == 0:
                sleep(settings.NO_QUEUES_WAIT_TIME_S)
            else:
                self.process_messages(queues, worker, static_queues)

    def process_messages(self, queues: list, worker: Worker, static_queues: list):
        for queue in queues:
            if self._exit_gracefully:
                return

            try:
                messages = self.poll_messages(queue)
                logger.debug('[django-eb-sqs] Polled {} messages'.format(len(messages)))

                self._send_signal(MESSAGES_RECEIVED, messages=messages)

                msg_entries = []
                for msg in messages:
                    self._execute_user_code(lambda: self._process_message(msg, worker))
                    msg_entries.append({
                        'Id': msg.message_id,
                        'ReceiptHandle': msg.receipt_handle
                    })

                self._send_signal(MESSAGES_PROCESSED, messages=messages)

                self.delete_messages(queue, msg_entries)

                self._send_signal(MESSAGES_DELETED, messages=messages)
            except ClientError as exc:
                error_code = exc.response.get('Error', {}).get('Code', None)
                if error_code == 'AWS.SimpleQueueService.NonExistentQueue' and queue not in static_queues:
                    logger.debug('[django-eb-sqs] Queue was already deleted {}: {}'.format(queue.url, exc),
                                 exc_info=True)
                else:
                    logger.warning('[django-eb-sqs] Error polling queue {}: {}'.format(queue.url, exc), exc_info=True)
            except Exception as exc:
                logger.warning('[django-eb-sqs] Error polling queue {}: {}'.format(queue.url, exc), exc_info=True)

            if timezone.now() - timedelta(
                    seconds=settings.MIN_HEALTHCHECK_WRITE_PERIOD_S) > self._last_healthcheck_time:
                self.write_healthcheck_file()
                self._last_healthcheck_time = timezone.now()

    def delete_messages(self, queue, msg_entries: list):
        if len(msg_entries) > 0:
            response = queue.delete_messages(Entries=msg_entries)

            # logging
            failed = response.get('Failed', [])
            num_failed = len(failed)
            if num_failed > 0:
                logger.warning('[django-eb-sqs] Failed deleting {} messages: {}'.format(num_failed, failed))

    def poll_messages(self, queue):
        return queue.receive_messages(
            MaxNumberOfMessages=settings.MAX_NUMBER_OF_MESSAGES,
            WaitTimeSeconds=settings.WAIT_TIME_S,
            AttributeNames=[self._RECEIVE_COUNT_ATTRIBUTE]
        )

    def _send_signal(self, dispatch_signal: django.dispatch.Signal, messages: list):
        if dispatch_signal.has_listeners(sender=self.__class__):
            self._execute_user_code(lambda: dispatch_signal.send(sender=self.__class__, messages=messages))

    def _process_message(self, msg, worker):
        logger.debug('[django-eb-sqs] Read message {}'.format(msg.message_id))
        try:
            receive_count = int(msg.attributes[self._RECEIVE_COUNT_ATTRIBUTE])

            if receive_count > 1:
                logger.warning('[django-eb-sqs] SQS re-queued message {} times - msg: {}'.format(
                    receive_count, msg.body
                ))

            worker.execute(msg.body)

            logger.debug('[django-eb-sqs] Processed message {}'.format(msg.message_id))
        except ExecutionFailedException as exc:
            logger.warning('[django-eb-sqs] Handling message {} got error: {}'.format(msg.message_id, repr(exc)))

    @staticmethod
    def _execute_user_code(function):
        try:
            with django_db_management():
                function()
        except Exception as exc:
            logger.error('[django-eb-sqs] Unhandled error: {}'.format(exc), exc_info=True)

    def write_healthcheck_file(self):
        with open(settings.HEALTHCHECK_FILE_NAME, 'w') as file:
            file.write(timezone.now().isoformat())

    def _exit_called(self, signum, frame):
        logger.info('[django-eb-sqs] Termination signal called: {}'.format(signum))
        self._exit_gracefully = True
