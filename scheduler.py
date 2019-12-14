import datetime
import schedule
from sqlalchemy.orm import sessionmaker
from crud import engine
from models import User
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()
Session = sessionmaker(bind=engine)

s = Session()
def increment_busyness():
    for user in s.query(User):
        date_from = user.busy_from_date
        date_to = user.busy_to_date
        now = datetime.date.today()
        if now >= date_from and now <= date_to:
            user.busyness_points += 4


@sched.scheduled_job('interval', seconds=5)
def timed_job():
    increment_busyness()


@sched.scheduled_job('cron', day_of_week='fri', hour=10)
def scheduled_job():
    increment_busyness()

sched.start()
