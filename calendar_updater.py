from telegram import Bot
import logging
import requests
from datetime import datetime
from dateutil import tz
import pandas as pd
import re
import locale
from seleniumwire import webdriver  # Import from seleniumwire instead of selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import asyncio

from random import randint
import time


locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")


class CalendarAPI:
    def __init__(self, base_url, params={}, cookies={}, headers={}):
        self.base_url = base_url
        self.cookies = cookies
        self.headers = headers
        self.params = params

    def fetch_events(self, year, month):
        json_data = [
            {
                "index": 0,
                "methodname": "core_calendar_get_calendar_monthly_view",
                "args": {
                    "year": str(year),
                    "month": str(month),
                    "courseid": 1,
                    "day": 1,
                    "view": "month",
                },
            }
        ]

        response = requests.post(
            self.base_url,
            params=self.params,
            cookies=self.cookies,
            headers=self.headers,
            json=json_data,
        )
        return response.json()[0].get("data", {})


class EventParser:
    @staticmethod
    def get_date(input_string):
        pattern = r"(\d{2}:\d{2})"
        match = re.search(pattern, input_string)
        return match.group(1) if match else "No match found"

    @staticmethod
    def date_formatter(date_str, lang="ru"):
        if lang == "ru":
            res = [
                val.capitalize() for val in date_str.replace("События - ", "").split()
            ]
            return f"{res[0]}, {' '.join(res[1:])}"
        elif lang == "en":
            return " ".join(
                [
                    val.strip().capitalize()
                    for val in date_str.replace("events", "").strip().split()
                ]
            )

    @staticmethod
    def flatten(lst):
        return [item for sublist in lst for item in sublist]


class EventDataProcessor:
    def __init__(self, data):
        self.data = data

    def extract_events(self)-> list:
        events = [
            [day for day in week.get("days", []) if day.get("hasevents")]
            for week in self.data.get("weeks", [])
        ]
        events_flat = EventParser.flatten(events)

        result = []
        for event in events_flat:
            for e in event.get("events", [{}]):
                if "Тест открывается" != e.get("activitystr"):
                    result.append(
                        [
                            event.get("viewdaylink", ""),
                            str(
                                datetime.fromtimestamp(
                                    event.get("timestamp"), tz=tz.gettz("GMT+3")
                                )
                            ),
                            event.get("viewdaylinktitle", ""),
                            e.get("activityname", ""),
                            e.get("viewurl"),
                            e.get("url", ""),
                            e.get("description", ""),
                            e.get("formattedtime"),
                            e.get("course", {}).get("fullnamedisplay"),
                            e.get("course", {}).get("viewurl", ""),
                        ]
                    )
        return result


class CalendarOutput:
    def __init__(self, events):
        self.events = events
        self.df = pd.DataFrame(events)
        self.df.columns = [
            "calendar_link",
            "date",
            "date_str",
            "name",
            "calendar",
            "hw_link",
            "description",
            "due_time",
            "subj",
            "subj_link",
        ]

    @staticmethod
    def to_bold(string) -> str:
        return f"*{string}*"

    @staticmethod
    def to_clickable_link(link_text, link) -> str:
        return f"[{link_text}]({link})"

    @staticmethod
    def get_russian_now() -> str:
        now = datetime.now()
        return " ".join(
            val.capitalize()
            for val in datetime.strftime(now, "%A, %d %B %Y %H:%M").split()
        )

    def generate_output(self, mnth_name: str):
        output = "😱👺💻" + self.to_bold(f" Домашка на {mnth_name} \n")
        output += (
            "📌 "
            + f'{self.to_bold("Время последнего обновления:")} {self.get_russian_now()} \n'
        )
        self.df: pd.DataFrame = self.df.sort_values("date").reset_index(drop=True)
        for dt in self.df.date_str.unique():
            output += "\n" + "📅 " + EventParser.date_formatter(dt) + "\n"
            cur_df = self.df[self.df.date_str == dt]
            cnt = 0
            for idx in range(len(cur_df)):
                cnt += 1
                if cnt > 1:
                    output += "\n"
                # output += self.to_clickable_link(cur_df.iloc[idx].subj, cur_df.iloc[idx].subj_link) + "\n"
                output += (
                    "✅ "
                    + self.to_bold(cur_df.iloc[idx].subj.split("(")[0].strip())
                    + "\n"
                )
                output += (
                    self.to_clickable_link(
                        cur_df.iloc[idx]["name"], cur_df.iloc[idx].hw_link
                    )
                    + "\n"
                )
                output += (
                    self.to_bold(
                        f"До {EventParser.get_date(cur_df.iloc[idx].due_time)}"
                    )
                    + "❗️"
                    + "\n"
                )

        return output


if __name__ == "__main__":
    # Specify the path to your WebDriver (e.g., ChromeDriver)
    driver_path = ''
    # xattr -d com.apple.quarantine chromedriver 

    # Create a new instance of the Chrome driver with Selenium Wire
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service)

    EMAIL, PASSWORD = '', ''
    
    try:
        # Open Google
        driver.get('https://edu.hse.ru/my/index.php?lang=ru')

        driver.find_element(By.CSS_SELECTOR, '.btn-secondary').click()
        time.sleep(randint(10, 20))

        # Find the login and password input fields
        login, password = driver.find_elements(By.CSS_SELECTOR, '.lgn-input__field')
        time.sleep(randint(1, 5))
        login.send_keys(EMAIL)
        time.sleep(randint(1, 5))
        password.send_keys(PASSWORD)
        time.sleep(randint(10, 15))

        # Wait for a few seconds to let the results load
        driver.find_element(By.CSS_SELECTOR, '.lgn-button').click()
        time.sleep(randint(10, 15))
        
        driver.get('https://edu.hse.ru/calendar/view.php?view=month')    
        driver.find_elements(By.CSS_SELECTOR, '.arrow_link')[1].click()
        time.sleep(randint(1, 5))

        # Iterate over the captured requests
        for request in driver.requests:
            if 'edu.hse.ru/lib/ajax/' in request.url and 'sesskey' in request.url:
                params = {val.strip().split('=', 1)[0].strip():val.strip().split('=', 1)[-1].strip() for val in request.url.split('?')[-1].split('&')}
                headers, cookies = request.headers, driver.get_cookies()

    finally:
        # Close the browser window
        driver.quit()
    
    headers = dict(headers)
    cookies = {headers['Cookie'].split('=')[0]:headers['Cookie'].split('=')[-1]}

    params = params
    
    print(headers, cookies, params, sep='\n')

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Replace 'YOUR_BOT_TOKEN' with your bot's API token
    TOKEN = ""
    # Replace '@your_channel_username' with your channel's username (e.g., '@my_channel')
    CHANNEL_ID = ""
    bot = Bot(token=TOKEN)
    api = CalendarAPI(
        base_url="https://edu.hse.ru/lib/ajax/service.php",
        params=params,
        cookies=cookies,
        headers=headers,
    )
    tie_mnth_msg_id = {9: 1129, 10: 1908, 11: 4822, 12: 6444, 1: 9257, 2:12082, 3:12808, 4:13485, 5:15086, 6:15713}
    tie_mnth_msg_name = {9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь", 1: 'Январь', 2: 'Февраль', 3:'Март', 4:'Апрель', 5:'Май', 6:'Июнь', 7:'Июль'}
    logger.info("Successfully connected to the API!")
    cur_mnth = datetime.now().month
    year = datetime.now().year
    for month in (cur_mnth, cur_mnth + 1):
        if month > 12: 
            month %= 12
            year = datetime.now().year + 1 
        logger.info(f"Currently processeed month number {month}!")
        data = api.fetch_events(year=year, month=month)
        processor = EventDataProcessor(data) 
        events = processor.extract_events()
    
        if not events:
            logger.warning(f"Dont have data for month number {month}")
        else:
            logger.info(f"Got {len(events)} new events!")
            calendar_output = CalendarOutput(events)
            if month == 2:
                print(events)
            output = calendar_output.generate_output(tie_mnth_msg_name.get(month))
            logger.info("Successfully generated output")
            # Send a message to the channel
            try:
                # Edit the message
                if tie_mnth_msg_id.get(month):
                    bot.edit_message_text(
                        chat_id=CHANNEL_ID,
                        parse_mode="markdown",
                        message_id=tie_mnth_msg_id.get(month),
                        text=output,
                    )
                    logger.info("Message edited successfully!")
                else:
                    msg = bot.send_message(
                        reply_to_message_id=tie_mnth_msg_id.get(12 if month == 1 else month - 1),
                        chat_id=CHANNEL_ID,
                        parse_mode="markdown",
                        text=output,
                    )
                    logger.info("Message sented successfully!")
                    logger.info(f"Message id {msg.message_id}")

            except Exception as e:
                logger.error(f"Failed to send or edit message: {e}")
