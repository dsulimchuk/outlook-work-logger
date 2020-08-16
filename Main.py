import os

import arrow
import requests
from ics import Calendar

DATE_FORMAT = 'YYYY-MM-DD'

CALENDAR_ICS = "https://mail1.crpt.ru/owa/calendar/dba53dda9bbc46448d2ce7be0a6844ea@crpt.ru/dae8e61158fb41c5bbbb4e61faa8b60c10009145121937266577/calendar.ics"


def download_calendar():
    response = requests.get(CALENDAR_ICS)
    if response.status_code != 200:
        print(response)
    return response.text


def log_work(name, begin, duration, desc, location):
    pass


def run():
    raw_calendar = download_calendar()
    calendar = Calendar(raw_calendar)
    print(f"Loaded {len(calendar.events)} events")
    cur_date = ask_date()
    events_at_date = list(filter(lambda d: d.begin.date() == cur_date.date(), calendar.events))
    if len(events_at_date) == 0:
        print(f"No events found at {cur_date.format(DATE_FORMAT)}")
    else:
        for event in events_at_date:
            location = event.location
            desc = event.description or "".strip()[0:100] + '...'
            name = event.name
            begin = event.begin
            duration = event.duration
            cls()
            print("##################################################################################")
            print(f"Event: {name}")
            print(f"Date: {begin.naive}")
            print(f"Duration: {duration}")
            print(f"Description: {desc}")
            while True:
                intent = input(f"Log work (l) or skip (s)?")
                if intent == 'l':
                    log_work(name, begin, duration, desc, location)
                    print("Logged!")
                    break
                elif intent == 's':
                    print("Skipped!")
                    break


def ask_date():
    cur_date = arrow.now()
    user_date_str = input(f"Enter date {DATE_FORMAT}. Default {cur_date.format(DATE_FORMAT)}>>>")
    if user_date_str != '':
        cur_date = arrow.get(user_date_str, DATE_FORMAT)
    return cur_date


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == '__main__':
    run()
