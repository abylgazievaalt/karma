import datetime

import schedule
from sqlalchemy.orm import sessionmaker
from crud import engine
from models import User

Session = sessionmaker(bind=engine)
s = Session()

def increment_busyness():
    for user in s.query(User):
        date_from = user.busy_from_date
        date_to = user.busy_to_date
        now = datetime.date.today()
        if now >= date_from and now <= date_to:
            user.busyness_points += 4


if __name__ == '__main__':
    schedule.every(5).seconds.do(increment_busyness)