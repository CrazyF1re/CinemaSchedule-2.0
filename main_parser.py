import db_manager
import schedule

manager = db_manager.manager()

def loop():
    
    manager.init_users_db()
    manager.init_db()
    manager.update_db()

schedule.every().day.at("13:00").do(loop)

loop()
while True:
    schedule.run_pending()
