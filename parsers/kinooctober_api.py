from bs4 import BeautifulSoup  as bs
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime,timedelta

base_url = 'https://kino-october.ru'
films_url = 'https://kino-october.ru/events?facility=oktyabr-123'

#returns list as [name_of_film, dictionary_of_schedule, url_to_film, img_url]
def get_films():
    res =[]
    driver = webdriver.Chrome()
    driver.get(films_url)
    soup = bs(driver.page_source)
    soup = soup.find('div',{'class':['rental']})
    images = [i.find('img')['src'] for i in soup.find_all('div',{'class':['event-poster']})]
    for film,age,img in zip(soup.find_all('h2',{'class':['title']}),soup.find_all('div',{'class':['age']}),images):
        url = base_url+film.find('a')['href']
        res.append([film.text+f" ({age.text})",get_schedule(driver,url),url,img])
    driver.close()
    return res
#returns schedule as {date : list_of_times&price,...}
def get_schedule(driver,url):
    res = {}
    d = datetime.strptime(url[url.index('date=')+5:url.index('&')],"%Y/%m/%d")
    driver.get(url)
    for _ in range(len(driver.find_elements(By.XPATH,'//a[starts-with(@class,"day-tab")]'))):
        res[f'{d.strftime("%d.%m.%Y")}'] = []
        soup = bs(driver.page_source,'html.parser')
        for time in soup.find_all('div',{'class':['show']}):
            if 'disabled' not in time['class']:
                t = time.find('div',{'class':['show-time']}).text
                p = time.find('div',{'class':['show-info']}).text[:-2]
                res[f'{d.strftime("%d.%m.%Y")}'].append([t, p])
        url = url.replace(str(f"{d.strftime("%Y/%m/%d")}"),str(f"{(d+timedelta(days=1)).strftime("%Y/%m/%d")}"))
        driver.get(url)
        d+= timedelta(days=1)
    return res