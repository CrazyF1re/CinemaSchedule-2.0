import db_manager
import schedule

manager = db_manager.manager()

def loop():
    
    manager.update_db()

schedule.every().day.at("13:00").do(loop)

loop()
while True:
    schedule.run_pending()
