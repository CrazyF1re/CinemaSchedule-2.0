from bs4 import BeautifulSoup  as bs
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime,timedelta
import requests
import re

base_url = 'https://kino.seversk.ru'
films_url = 'https://kino.seversk.ru/trailer'
#returns list as [name_of_film, dictionary_of_schedule, url_to_film, img_url]
def get_films():
    res = []
    driver = webdriver.Chrome()
    driver.get(films_url)
    driver.maximize_window()
    soup = bs(driver.page_source, 'html.parser')
    for name,age in zip(soup.find_all(class_ = 'poster-item__info-title'),soup.find_all(class_ = 'film__label')):
        if requests.get(base_url+name['href']).status_code != 200:
            continue
        res.append([
            name.text.rstrip()+' (' + age.text +')',
            get_schedule(driver,base_url+name['href'],age.text[:-1]),
            base_url+name['href'],
            get_img(driver,base_url+name['href'])
            ])
    
    driver.close()
    return res
#returns schedule as {date : list_of_times&price,...}
def get_img(driver, url):
    soup = bs(driver.page_source,'html.parser')
    return soup.find_all('img',alt = 'Poster')[-1]['src']

def get_schedule(driver,url,age):
    res = {}
    driver.get(url)
    # capcha 18+
    if age=='18':
        try:
            driver.find_element(By.XPATH,'//a[@class="gradient-button-white redirect-forward"]').click()
        except:
            pass
    d = datetime.today()
    # get schedule of current day
    soup = bs(driver.page_source,'html.parser')
    res[f'{d.strftime("%d.%m.%Y")}'] = []
    for time in soup.find_all('div',{'data-film-date':[f'{d.strftime("%d.%m.%Y")}']}):
        if(len(time['class'])<3):
            price = re.sub("[^0-9]","",time.find('div',{'class': 'session-picker__item-price'}).text)
            res[f'{d.strftime("%d.%m.%Y")}'].append([
                time.find('div',{'class':['value']}).text.strip(),
                price
                ])
    driver.find_element(By.XPATH,'//span[@class="input-group-addon"]').click()
    length = len([i for i in driver.find_elements(By.CLASS_NAME, 'day') if 'disabled' not in i.get_attribute('class')])
    for _ in range(length-1):
        d+=timedelta(days=1)
        driver.get(f"{url}?date={d.strftime('%d.%m.%Y')}")
        soup = bs(driver.page_source,'html.parser')
        res[f"{d.strftime('%d.%m.%Y')}"]= []
        for time in soup.find_all('div',{'data-film-date':[f'{d.strftime("%d.%m.%Y")}']}):
            price = re.sub("[^0-9]","",time.find('div',{'class': 'session-picker__item-price'}).text)
            res[f"{d.strftime('%d.%m.%Y')}"].append([
                time.find('div',{'class':['value']}).text.strip(),
                price
            ])
    return res