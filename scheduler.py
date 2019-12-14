from bot import increment_busyness
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

@sched.scheduled_job('interval', seconds=5)
def timed_job():
    increment_busyness

@sched.scheduled_job('cron', day_of_week='fri', hour=10)
def scheduled_job():
    increment_busyness

sched.start()
