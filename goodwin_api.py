from bs4 import BeautifulSoup  as bs
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime,timedelta
import re


base_url = 'https://goodwincinema.ru'
films_url = 'https://goodwincinema.ru/affiche/'
#returns list as [name_of_film, dictionary_of_schedule, url_to_film,img_url]
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
#returns schedule as {date : list_of_times&price,...}
def get_schedule(url,driver ):
    res = {}    #returnable variable
    driver.get(url)#get page
    soup = bs(driver.page_source,'html.parser')# soup  to find information
    soup = soup.find('div',{'id':['schedule-container']})
    day = datetime.today()
    res[day.strftime("%d.%m.%Y")] = []#first init  
    
    #get schedule for today
    for seans in  soup.find_all('ul', {'class':['hall']}):
        for line in seans.find_all('li', {'class':['schedule-item']}):
            price = line.find('div', {'class':['price']})
            if price == None:
                continue
            price = re.sub("[^0-9]","",price.text)
            time = line.find('a',{'class':['time']}).text
            res[day.strftime("%d.%m.%Y")].append([time,price])
    #get schedule for the next days
    for i in driver.find_elements(By.XPATH,'//li[@class=""]'):
        i.click()#click on day
        day += timedelta(days=1)
        soup  =bs(driver.page_source,'html.parser')
        soup = soup.find('div',{'id':['schedule-container']})#get schedule block
        res[day.strftime("%d.%m.%Y")] = []#init 
        #same cycle in choosen day to get and write schedule
        for seans in  soup.find_all('ul', {'class':['hall']}):
            for line in seans.find_all('li', {'class':['schedule-item']}):
                price = line.find('div', {'class':['price']})
                if price == None:
                    continue
                price = re.sub("[^0-9]","",price.text)
                time = line.find('a',{'class':['time']}).text
                res[day.strftime("%d.%m.%Y")].append([time,price])
    return res