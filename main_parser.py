import db_manager
import schedule
from my_schedule import scheduler

manager = db_manager.manager()
scheduler_instance = scheduler()

def loop():
    manager.update_db()
    try:
        scheduler_instance.check_films()
    except:
        pass

schedule.every().day.at("13:00").do(loop)

# loop()
scheduler_instance.check_films()
while True:
    schedule.run_pending()
