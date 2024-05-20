from fastapi import FastAPI, Request, Response,Form, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import MetaData,insert
from urllib.parse import unquote
from datetime import datetime
from fastapi.responses import RedirectResponse
from db_manager import manager
import bcrypt
from typing import Annotated
import jwt

app = FastAPI()
templates = Jinja2Templates(directory='templates')
database = manager()

SECRET = "SECRET"

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get('/')
def get_main(request: Request):
    engine = database.film_engine
    meta = MetaData()
    meta.reflect(engine)
    film_table = meta.tables['film_table']
    
    if (request.cookies.get('cinemas')):
        try:
            cinemas = [int(i) for i in request.cookies.get('cinemas').split(',')]
        except:
            cinemas = [1,2,3,4,5]
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
    engine = database.film_engine
    meta = MetaData()
    meta.reflect(engine)
    film_table = meta.tables['film_table']
    sessions_table = meta.tables['sessions_table']

    with engine.connect() as connection:
        all_sessions = []
        all_sessions.append(unquote(film))
        all_sessions.append(connection.execute(film_table.select()
                                    .where(film_table.c.name == unquote(film))
                                    .with_only_columns(film_table.c.img_url))
                                    .fetchone()[0])
        all_sessions.append([])
        all_sessions.append({})
        for cinema in cinemas:   
            film_id = connection.execute(film_table.select()
                                    .where(film_table.c.name == unquote(film))
                                    .where(film_table.c.cinema_id == cinema)
                                    .with_only_columns(film_table.c.id)).fetchone()
            if (film_id):
                film_url = connection.execute(film_table.select()
                                          .where(film_table.c.cinema_id == cinema)
                                          .where(film_table.c.name == unquote(film))
                                          .with_only_columns(film_table.c.url)).fetchone()
                sessions =connection.execute(sessions_table.select()
                                        .where(sessions_table.c.film_id == film_id[0])
                                        .where(sessions_table.c.datetime > datetime.now())
                                        .with_only_columns(sessions_table.c.datetime,sessions_table.c.price)).fetchall()
                all_sessions[2].append({cinema:sessions})
                all_sessions[3][cinema] = film_url
    return templates.TemplateResponse(request=request, name='film.html',context={"info":all_sessions})
    
@app.get('/login')
def login(request: Request):
    if (request.cookies.get('token')):
        return RedirectResponse('/')
    return templates.TemplateResponse(request=request, name='login.html')

@app.get('/register')
def register(request: Request):
    if (request.cookies.get('token')):
        return RedirectResponse('/')
    return templates.TemplateResponse(request=request, name='register.html')

@app.post('/register')
async def register_user( email: Annotated[str, Form()], password: Annotated[str, Form()], request: Request):
    engine = database.user_engine
    meta = MetaData()
    meta.reflect(engine)
    users = meta.tables['user']
    with engine.connect() as connection:
        if(connection.execute(users.select().where(users.c.email == email)).fetchone()):
            print('пользователь уже существует')
            return templates.TemplateResponse(request=request,name='register.html', context={"bad":True})
        connection.execute(insert(users).values(email = email, hashed_password = bcrypt.hashpw(str.encode(password),bcrypt.gensalt())))
        connection.commit()
        user_id = connection.execute(users.select().where(users.c.email == email).with_only_columns(users.c.id)).fetchone()[0]
    
    #get JWT to user
    encoded_jwt = jwt.encode({"id": user_id, "email":email}, SECRET, algorithm="HS256")
    #set JWT into cookie
    res = RedirectResponse('/', status_code= status.HTTP_302_FOUND)
    res.set_cookie(key="token",value=encoded_jwt, httponly=True)
    return res


@app.post('/login')
async def login_user(email: Annotated[str, Form()], password: Annotated[str, Form()],request: Request):
    #validate user
    engine = database.user_engine
    meta = MetaData()
    meta.reflect(engine)
    users = meta.tables['user']
    with engine.connect() as connection:
        user_info = connection.execute(users.select().where(users.c.email == email).with_only_columns(users.c.hashed_password, users.c.id)).fetchone()
        if(user_info and bcrypt.checkpw(str.encode(password), user_info[0])):
            encoded_jwt = jwt.encode({"id": user_info[1], "email": email}, SECRET, algorithm="HS256")
            res = RedirectResponse('/', status_code= status.HTTP_302_FOUND)
            res.set_cookie(key="token",value=encoded_jwt, httponly=True)
            return res
        return templates.TemplateResponse(request=request,name='login.html', context={"bad":True})

@app.post('/logout')
async def logout_user(response:Response):
    resp = RedirectResponse('/', status_code= status.HTTP_302_FOUND)
    resp.delete_cookie('token')
    return resp
    #check cookies and look for JWT token
    #logout user if token was founded
    #return some template if user has no token
    pass
