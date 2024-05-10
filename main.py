from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, MetaData


app = FastAPI()
templates = Jinja2Templates(directory='templates')

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get('/')
def get_main(request: Request):
    engine = create_engine('sqlite:///database.db')
    meta = MetaData()
    meta.reflect(engine)
    film_table = meta.tables['film_table']
    sessions_table = meta.tables['sessions_table']
    
    if (request.cookies.get('cinemas')):
        cinemas = [int(i) for i in request.cookies.get('cinemas').split(',')]
        with engine.connect() as connection:
            films = connection.execute(film_table.select().group_by(film_table.c.name).where(film_table.c.img_url !='' and film_table.c.id_cinema.in_(cinemas)).with_only_columns(film_table.c.name,film_table.c.img_url,film_table.c.url)).fetchall()
    else:
        with engine.connect() as connection:
            films = connection.execute(film_table.select().group_by(film_table.c.name).where(film_table.c.img_url !='').with_only_columns(film_table.c.name,film_table.c.img_url,film_table.c.url)).fetchall()     
    
    
    
    return templates.TemplateResponse(request=request, name='main.html',context={"films":films})