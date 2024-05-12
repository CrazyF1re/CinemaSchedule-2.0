from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, MetaData
from urllib.parse import unquote
from sqlalchemy.orm import sessionmaker

app = FastAPI()
templates = Jinja2Templates(directory='templates')

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get('/')
def get_main(request: Request):
    engine = create_engine('sqlite:///database.db')
    meta = MetaData()
    meta.reflect(engine)
    film_table = meta.tables['film_table']
    
    if (request.cookies.get('cinemas')):
        cinemas = [int(i) for i in request.cookies.get('cinemas').split(',')]
        with engine.connect() as connection:
            films = connection.execute(film_table.select().group_by(film_table.c.name)
                                       .where(film_table.c.img_url !='')
                                       .where(film_table.c.cinema_id.in_(cinemas))
                                       .with_only_columns(film_table.c.name,film_table.c.img_url)).fetchall()
    else:
        with engine.connect() as connection:
            films = connection.execute(film_table.select().group_by(film_table.c.name)
                                       .where(film_table.c.img_url !='')
                                       .with_only_columns(film_table.c.name,film_table.c.img_url)).fetchall()     
    
    return templates.TemplateResponse(request=request, name='main.html',context={"films":films})

@app.get('/films/{film}/')
def get_film(request:Request,film):
    if(request.cookies.get('cinemas')):
        cinemas = [int(i) for i in request.cookies.get('cinemas').split(',')]
    else:
        cinemas = [1,2,3,4,5]
    engine = create_engine('sqlite:///database.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    meta = MetaData()
    meta.reflect(engine)
    film_table = meta.tables['film_table']
    sessions_table = meta.tables['sessions_table']

    with engine.connect() as connection:
        all_sessions = []
        all_sessions.append(unquote(film))
        print(all_sessions[0])
        all_sessions.append(connection.execute(film_table.select()
                                    .where(film_table.c.name == unquote(film))
                                    .with_only_columns(film_table.c.img_url))
                                    .fetchone()[0])
        all_sessions.append([])
        for cinema in cinemas:   
            film_id = connection.execute(film_table.select()
                                    .where(film_table.c.name == unquote(film))
                                    .where(film_table.c.cinema_id == cinema)
                                    .with_only_columns(film_table.c.id)).fetchone()
            if (film_id):
                sessions =connection.execute(sessions_table.select()
                                        .where(sessions_table.c.film_id == film_id[0])
                                        .with_only_columns(sessions_table.c.datetime,sessions_table.c.price)).fetchall()
                all_sessions[2].append({cinema:sessions})
    print(all_sessions)
    return templates.TemplateResponse(request=request, name='film.html',context={"info":all_sessions})
    