import asyncio

import selenium.common
from modules.DataBase import DataBase
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base import ParserBase
import warnings
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By


class Eezy(ParserBase):

    def __init__(self, url='https://tyopaikat.eezy.fi/en'):
        super().__init__()
        self.url = url
        self.orm = DataBase('data/database.db')

    async def accept_cookies(self, driver):
        try:
            cookies = driver.find_element(By.CLASS_NAME, 'ch2-deny-all-btn')
            cookies.click()
        except selenium.common.exceptions.NoSuchElementException:
            pass

    async def parse_by_selenium(self, keyword='', location=''):
        warnings.warn("This function is deprecated.", DeprecationWarning)

        driver = await self.get_driver()
        driver.get(url=f"{self.url}?job={keyword}&location={location}")

        await self.accept_cookies(driver)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'css-1u0wjtf'))
        )

        content_block = driver.find_element(By.CLASS_NAME, 'css-1u0wjtf')
        show_more_buttons = driver.find_elements(By.CLASS_NAME, 'css-17kp6u6')

        for button in show_more_buttons:
            button.click()
            time.sleep(1)

        vacancies = content_block.find_elements(By.CLASS_NAME, 'css-7x9j97')

        if len(vacancies) == 0:
            raise Exception("Vacancies weren't found")

        for i, vacancy in enumerate(vacancies):
            print(vacancy.text + "\n")

            try:
                link = vacancy.find_element(By.TAG_NAME, 'a').get_attribute('href')
                title = vacancy.find_element(By.CLASS_NAME, 'css-x9gms1').text
                location = vacancy.find_element(By.CLASS_NAME, 'css-1o7vf0g').text
                description = self.get_description(driver, link)
                self.orm.save_vacancy(
                    table=Eezy.__name__,
                    slug=link.replace('https://tyopaikat.eezy.fi', ''),
                    title=title,
                    description=description,
                    locations={"location": location}
                )
            except (NoSuchElementException, StaleElementReferenceException) as ex:
                print("Error processing vacancy:", ex)

    async def get_description(self, driver, link):
        driver.get(link)
        description_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'css-aofzs'))
        )
        description = description_element.find_element(By.CLASS_NAME, 'css-4cffwv').text
        return description.strip()[:400] + "..."

    async def parse_by_bs4(self, keyword="", location=""):
        driver = await self.get_driver()

        driver.get(url=f"{self.url}?job={keyword}&location={location}")

        await self.accept_cookies(driver=driver)

        await asyncio.sleep(1)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'css-1u0wjtf'))
        )

        while True:
            try:
                driver.find_element(By.CLASS_NAME, 'css-17kp6u6').click()
                await asyncio.sleep(1)
            except NoSuchElementException:
                break

        soup = BeautifulSoup(driver.page_source, "lxml")

        vacancies = soup.find_all("div", class_="css-7x9j97")

        for vacancy in vacancies:
            slug = vacancy.find("a").get("href")
            link = f"https://tyopaikat.eezy.fi{slug}"
            title = vacancy.find("div", class_='css-x9gms1').text
            location = vacancy.find("div", class_="css-1o7vf0g").text if vacancy.find("div",
                                                                                      class_="css-1o7vf0g") else None
            description = await self.get_description(driver=driver, link=link)

            await self.orm.save_vacancy(
                table=Eezy.__name__,
                slug=slug,
                title=title,
                description=description,
                locations={"location": location}
            )

        driver.close()
        driver.quit()

