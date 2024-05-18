import db_manager
import schedule



def loop():
    manager = db_manager.manager()
    manager.init_users_db()
    manager.init_db()
    manager.update_db()

schedule.every().day.at("13:00").do(loop)

loop()
while True:
    schedule.run_pending()
