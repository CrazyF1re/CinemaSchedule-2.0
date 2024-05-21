import parsers.goodwin_api
import parsers.kinomax_api
import parsers.kinooctober_api
import parsers.kinopolis_api
import parsers.kinoseversk_api
from sqlalchemy import MetaData,Table,Column,Integer,String,create_engine,ForeignKey,Date,DateTime,text,insert,select,Boolean
from sqlalchemy_utils import create_database
from sqlalchemy.sql.expression import bindparam

from datetime import datetime
import os


class manager():
    def __init__(self):
        self.user_engine = create_engine("sqlite:///databases/user.db")
        self.film_engine = create_engine('sqlite:///databases/flims.db')
        self.message_engine = create_engine('sqlite:///databases/send_message.db')
        self.init_films_db()
        self.init_users_db()
        self.init_send_message_db()
    def init_films_db(self):
        if(not os.path.isfile('./databases/films.db')):
            create_database(self.film_engine.url)
            meta = MetaData()
            cinema_table = Table(
                'cinema_table',meta,
                Column('id',Integer,primary_key=True),
                Column('name',String),
            )
            film_table = Table(
                'film_table',meta,
                Column('id',Integer,primary_key=True),
                Column('name',String),
                Column('url',String),
                Column('img_url',String),
                Column('cinema_id',Integer,ForeignKey("cinema_table.id")),
            )
            sessions_table = Table(
                'sessions_table',meta,
                Column('film_id',Integer,ForeignKey("film_table.id")),
                Column('datetime', DateTime),
                Column('price',Integer),
            )
            meta.create_all(self.film_engine)
            with self.film_engine.connect() as connection:
                connection.execute(insert(cinema_table).values([  
                        {'name':"Goodwin Cinema"},
                        {'name':"Kinomax"},
                        {'name':"Kinooctober"},
                        {'name':"Kinopolis"},
                        {'name':"Kinoseversk"}]))
                connection.commit()

    def init_users_db(self):
        if(not os.path.isfile('./databases/user.db')):
            create_database(self.user_engine.url)
            meta = MetaData()
            users = Table(
                    'user',meta,
                    Column('id',Integer,primary_key=True),
                    Column('email',String),
                    Column('hashed_password',String)
                )
            meta.create_all(self.user_engine)

    def init_send_message_db(self):
        if(not os.path.isfile('./databases/send_message.db')):
            create_database(self.message_engine.url)
            meta = MetaData()
            user = Table('users', meta,
                          Column('id', Integer),
                          Column('email',String),
                          Column('film',String))
            meta.create_all(self.message_engine)

    def update_db(self):
        res = {}

        functions = [parsers.goodwin_api.get_films,
                     parsers.kinomax_api.get_films,
                     parsers.kinooctober_api.get_films,
                     parsers.kinopolis_api.get_films,
                     parsers.kinoseversk_api.get_films
                     ]
        i = 1
        for func in functions:
            res[i]=func()
            i+=1

        #refill database with fresh data
        engine = self.film_engine
        meta = MetaData()
        meta.reflect(engine)
        film_table = meta.tables['film_table']
        sessions_table = meta.tables['sessions_table']
        with engine.connect() as connection:
            connection.execute(text("DELETE FROM film_table"))
            connection.execute(text("DELETE FROM sessions_table"))
            connection.commit()
            film_table_data = []
            sessions_table_data= []
            for cinema,films in res.items():
                for film in films:
                    film_table_data.append({"name":film[0],"img_url":film[3], "url":film[2], "cinema_id":cinema})

            connection.execute(insert(film_table).values({
                "name":bindparam('name'),
                'img_url':bindparam('img_url'),
                'url':bindparam('url'),
                'cinema_id':bindparam('cinema_id')
            }),film_table_data)
            connection.commit()  

            for cinema,films in res.items():
                for film in films:
                    film_id = connection.execute(select(film_table.c.id).where(film_table.c.name == film[0],film_table.c.cinema_id == cinema)).fetchone()[0]
                    for date,times in film[1].items():
                        for time in times:
                            film_time = datetime.strptime( f'{date} {time[0]}',"%d.%m.%Y %H:%M")
                            sessions_table_data.append({"film_id":film_id,"datetime":film_time,"price":time[1]})
            
            connection.execute(insert(sessions_table).values({
                "film_id":bindparam('film_id'),
                'datetime':bindparam('datetime'),
                'price':bindparam('price')
            }),sessions_table_data)
            connection.commit()
    
        


    