from sqlalchemy import MetaData,create_engine
from difflib import SequenceMatcher
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import time

class scheduler:
    def __init__(self):
        self.my_mail = 'cinema.schedule@mail.ru'
        self.mail_password = 'fKV9N7HLq9gsst0sff9e'
        self.message_engine = create_engine('sqlite:///databases/send_message.db')
        self.film_engine = create_engine('sqlite:///databases/flims.db')
        self.smtp_server = smtplib.SMTP_SSL('smtp.mail.ru', 465)
        self.smtp_server.login(self.my_mail, self.mail_password)

    def check_films(self):
        meta_film = MetaData()
        meta_users = MetaData()
        meta_film.reflect(self.film_engine)
        meta_users.reflect(self.message_engine)
        film_table = meta_film.tables['film_table']
        users = meta_users.tables['users']
        with self.film_engine.connect() as connection:
            films = connection.execute(film_table.select().group_by(film_table.c.name).with_only_columns(film_table.c.name, film_table.c.img_url)).fetchall()
        with self.message_engine.connect() as connection:
            users = connection.execute(users.select().with_only_columns(users.c.email, users.c.film)).fetchall()
        for film in films:
            for user_info in users:
                cur_film = film[0][:-5].rstrip()
                if (SequenceMatcher(None,cur_film.lower(),user_info[1].lower()).ratio()>0.6):
                    self.send_message(user_info[0],cur_film, film[1])
        
    def send_message(self,email,film, img_url):
        msg = MIMEMultipart()
        msg["From"] = self.my_mail
        msg["To"] = email
        msg["Subject"] = "Рассылка Cinema Schedule"
        text = f"<h1>В прокате появился фильм {film}</h1> <img src='{img_url}' alt='{film}' style='width:400px'>"
        msg.attach(MIMEText(text,'html'))
        self.smtp_server.sendmail(self.my_mail, email, msg.as_string())