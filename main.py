from fastapi import FastAPI, Request,Form, status
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
from config import JWT_KEY

app = FastAPI()
templates = Jinja2Templates(directory='templates')
database = manager()



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
            
    context = {"films":films, 'token':False}
    if request.cookies.get('token'):
        context['token'] = True
    return templates.TemplateResponse(request=request, name='main.html',context=context)

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
    context = {"info":all_sessions, 'token' :False}
    if request.cookies.get('token'):
        context['token'] = True
    return templates.TemplateResponse(request=request, name='film.html',context=context)
    
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


@app.get('/lk')
def lk(request:Request):
    if (request.cookies.get('token')):
        lst = jwt.decode(request.cookies.get('token'), JWT_KEY, algorithms=["HS256"])
        
        email = lst['email']
        engine = database.message_engine
        meta = MetaData()
        meta.reflect(engine)
        user = meta.tables['users']
        with engine.connect() as connection:
            films = connection.execute(user.select().where(user.c.id == lst['id']).with_only_columns(user.c.film)).fetchall()
        #get info about planned sending emails 
        return templates.TemplateResponse(request=request, name='lk.html', context={'email':email,'films':films, 'token':True})
    return RedirectResponse('/')
    

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
    encoded_jwt = jwt.encode({"id": user_id, "email":email}, JWT_KEY, algorithm="HS256")
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
            encoded_jwt = jwt.encode({"id": user_info[1], "email": email}, JWT_KEY, algorithm="HS256")
            res = RedirectResponse('/', status_code= status.HTTP_302_FOUND)
            res.set_cookie(key="token",value=encoded_jwt, httponly=True)
            return res
        return templates.TemplateResponse(request=request,name='login.html', context={"bad":True})


@app.post('/logout')
async def logout_user():
    resp = RedirectResponse('/', status_code= status.HTTP_302_FOUND)
    resp.delete_cookie('token')
    return resp


@app.post('/film/delete')
async def delete_sending_message(request:Request,films:Annotated[list,Form()] = None):
    print(films)
    if(films == None):
        return RedirectResponse('/lk',status_code= status.HTTP_302_FOUND)    
    info = jwt.decode(request.cookies.get('token'), JWT_KEY, algorithms=["HS256"])
    id,email = info['id'],info['email']
    engine = database.message_engine
    meta = MetaData()
    meta.reflect(engine)
    user = meta.tables['users']
    with engine.connect() as connection:
        connection.execute(user.delete().where(user.c.id == id).where(user.c.email == email).where(user.c.film.in_(films)))
        connection.commit()
    return RedirectResponse('/lk',status_code= status.HTTP_302_FOUND)



@app.post('/lk/delete')
async def delete_account(request:Request):
    if(request.cookies.get('token')):
        id = jwt.decode(request.cookies.get('token'), JWT_KEY, algorithms=["HS256"])['id']
        engine = database.user_engine
        meta = MetaData()
        meta.reflect(engine)
        users = meta.tables['user']
        with engine.connect() as connection:
            connection.execute(users.delete().where(users.c.id == id))
            connection.commit()
        engine = database.message_engine
        meta.reflect(engine)
        users = meta.tables['users']
        with engine.connect() as connection:
            connection.execute(users.delete().where(users.c.id == id))
            connection.commit()
        resp = RedirectResponse('/', status_code= status.HTTP_302_FOUND)
        resp.delete_cookie('token')
        
        return resp


@app.post('/film/add_film')
async def add_film(request:Request, film: Annotated[str , Form()]= None):
    if film==None:
        return RedirectResponse('/lk',status_code= status.HTTP_302_FOUND)
    info = jwt.decode(request.cookies.get('token'), JWT_KEY, algorithms=["HS256"])
    id,email = info['id'],info['email']
    print(id,email)
    engine = database.message_engine
    meta = MetaData()
    meta.reflect(engine)
    user = meta.tables['users']
    with engine.connect() as connection:
        connection.execute(insert(user).values(id = id, email = email, film = film))
        connection.commit()
    return RedirectResponse('/lk',status_code= status.HTTP_302_FOUND)

