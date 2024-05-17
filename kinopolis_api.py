from bs4 import BeautifulSoup  as bs
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime,timedelta
import re

base_url = 'https://kino-polis.ru'
films_url = 'https://kino-polis.ru/affiche/'

#returns list as [name_of_film, dictionary_of_schedule, url_to_film, img_url]
def get_films():
    res = []
    driver = webdriver.Chrome()
    driver.get(films_url)
    images = [base_url+i.find('img')['src'] for i in bs(driver.page_source, 'html.parser').find_all('div',{'class':['img']})]
    for film,img in zip(bs(driver.page_source,'html.parser').find_all(class_ = 'film-title'),images):
        res.append([
            film.text.strip("\n").replace('  ',' ').replace('(в рамках Киноклуба) ',''),
            get_schedule(driver,base_url+film.find('a')['href'] ),
            base_url+film.find('a')['href'],
            img
            ])
    driver.close()
    return res
#returns schedule as {date : list_of_times&price,...}
def get_schedule(driver, url):
    res = {}
    driver.get(url)
    d = datetime.today()
    soup = bs(driver.page_source,'html.parser')
    res[d.strftime("%d.%m.%Y")] = []
    for seans in  soup.find_all('ul', {'class':['hall']}):
        for line in seans.find_all('li', {'class':['schedule-item']}):
            if 'disabled' in line['class']:
                continue
            price = line.find('span', {'class':['price_show']})
            if price == None:
                continue
            price = price = re.sub("[^0-9]","",price.text)
            time = line.find('a',{'class':['time']}).text
            res[d.strftime("%d.%m.%Y")].append([time,price])

    for i in driver.find_elements(By.XPATH,'//li[@class=""]'):
        i.click()#click on day
        d += timedelta(days=1)
        soup  =bs(driver.page_source,'html.parser')
        res[d.strftime("%d.%m.%Y")] = []
        for seans in  soup.find_all('ul', {'class':['hall']}):
            for line in seans.find_all('li', {'class':['schedule-item']}):
                if 'disabled' in line['class']:
                    continue
                price = line.find('span', {'class':['price_show']})
                if price == None:
                    continue
                price = price = re.sub("[^0-9]","",price.text)
                time = line.find('a',{'class':['time']}).text
                res[d.strftime("%d.%m.%Y")].append([time,price])
    return res