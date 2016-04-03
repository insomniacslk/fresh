import asyncio
import threading

import ipyparallel as parallel

from . import task_queue, utils

_scheduler = None

logger = utils.get_logger(__name__)


class Scheduler(threading.Thread):
    '''
    Task scheduler

    This class implements the task scheduler for submitting and executing new
    tasks
    '''

    def __init__(self):
        self._task_queue = task_queue.get()
        self._client = None
        self._running = False
        logger.debug('Initialized scheduler')
        threading.Thread.__init__(self)

    def enqueue(self, task):
        '''
        Add a new task to the queue and start processing it.

        A task must be a subclass of `fresh.task.Task`.
        '''
        logger.debug('Adding task: {t}'.format(t=task))
        self._task_queue.put_nowait(task)

    def enqueue_many(self, tasks):
        '''
        Add multiple tasks to the task queue, and start processing them.

        `tasks` is an iterable of Task subclasses.
        '''
        logger.debug('Adding {n} tasks: {t}'.format(
            n=len(tasks),
            t=str(tasks)[:30],
        ))
        for task in tasks:
            self._task_queue.put_nowait(task)

    def _connect(self):
        '''
        Connect to the IPyParallel cluster
        '''
        logger.info('Connecting to the ipyparallel cluster')
        self._client = parallel.Client()

    def run(self):
        logger.info('Starting task scheduler')
        self._connect()
        self._running = True
        lview = self._client.load_balanced_view()
        pending = set()
        while self._running:
            # wait for completed tasks from the client
            try:
                self._client.wait(pending, 1e-3)
            except parallel.TimeoutError:
                pass

            # update finished and pending task sets
            finished = pending.difference(self._client.outstanding)
            pending = pending.difference(finished)

            # add new tasks from the queue
            new_tasks = []
            while True:
                try:
                    new_tasks.append(self._task_queue.get_nowait())
                except asyncio.QueueEmpty:
                    break
            amr = lview.map(lambda t: t.start(), new_tasks)
            if amr:
                pending = pending.union(set(amr.msg_ids))

            # do something with the completed tasks
            for msg_id in finished:
                for result in self._client.get_result(msg_id).get():
                    logger.info('Result: {r!r}'.format(r=result))

    def stop(self):
        self._running = False

    def is_running(self):
        return self.running is True


def get():
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler
