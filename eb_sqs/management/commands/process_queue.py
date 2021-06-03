from django.core.management import BaseCommand, CommandError
from django.utils.module_loading import import_string

from eb_sqs import settings
from eb_sqs.worker.service import WorkerService


class Command(BaseCommand):
    help = 'Command to process tasks from one or more SQS queues'

    def add_arguments(self, parser):
        parser.add_argument('--queues', '-q',
                            dest='queue_names',
                            help='Name of queues to process, separated by commas')

    def handle(self, *args, **options):
        if not options['queue_names']:
            raise CommandError('Queue names (--queues) not specified')

        queue_names = [queue_name.rstrip() for queue_name in options['queue_names'].split(',')]

        queue_client_class = import_string(settings.QUEUE_CLIENT_CLASS)

        queue_client = queue_client_class()
        WorkerService(queue_client).process_queues(queue_names)
