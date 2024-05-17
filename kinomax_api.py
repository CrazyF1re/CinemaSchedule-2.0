from bs4 import BeautifulSoup  as bs
from selenium import webdriver

base_url = 'https://kinomax.tomsk.ru'
films_url = 'https://kinomax.tomsk.ru/affiche/'

#returns schedule as {date : list_of_times&price,...}
def get_schedule(url, driver):
    res = {}
    driver.get(url)
    soup = bs(driver.page_source,'html.parser')
    for line in soup.find_all('div', {'class': ['seance_line']}):
        for column in line.find_all('div', {'class': ['collumn']}):
            if column.find('div',{'class':['item']})!= None:
                for seans in column.find_all('div',{'class':['item']}):
                    if res.get(column['data-date']) == None:
                        res[column['data-date']] = []
                    text = seans.text.split()
                    res[column['data-date']].append([text[0],text[-2]]) 
    return res
#returns list as [name_of_film, dictionary_of_schedule, url_to_film, img_url]
def get_films():
    res = []
    driver = webdriver.Chrome()
    driver.get(films_url)
    soup = bs(driver.page_source,'html.parser')
    images = [base_url+i.find('img')['src'] for i in soup.find_all('div',{'class':['img']})]

    for film,img in zip(soup.find_all('div',{'class':['film-title']}),images):
       res.append([
           str(film.text.split('(')[0].strip() + ' (' + film.text.split('(')[-1]).replace("\n",""),
           get_schedule(base_url+film.find('a')['href'],driver),
           base_url+film.find('a')['href'],
           img
           ])  
    driver.close()
    return res