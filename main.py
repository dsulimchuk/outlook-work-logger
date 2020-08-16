import getpass
import logging
import os

import arrow
import keyring
import requests
from ics import Calendar as icsCalendar

from jiraClient import JiraClient

# TODO: Externalize
JIRA_URL = "https://jira.crpt.ru/"
JIRA_USER = "d.sulimchuk"
PROJECT = "MDLP"
JIRA_ISSUE = "MDLP-13243"
DATE_FORMAT = 'YYYY-MM-DD'
CALENDAR_ICS = ""


def download_calendar():
    if CALENDAR_ICS == "":
        raise RuntimeError(f"Provide link to download isc file (CALENDAR_ICS)")
    response = requests.get(CALENDAR_ICS)
    if response.status_code != 200:
        logging.error(response)
        logging.error(f"Headers:{response.headers}")
        logging.error(f"Body:{response.text}")
        raise RuntimeError(f"Unable to download calendar from {CALENDAR_ICS}")
    return response.text


def run():
    jira_client = init_jira()
    raw_calendar = download_calendar()
    calendar = icsCalendar(raw_calendar)
    print(f"Loaded {len(calendar.events)} events")
    cur_date = ask_date()
    events_at_date = list(filter(lambda d: d.begin.date() == cur_date.date(), calendar.events))
    if len(events_at_date) == 0:
        print(f"No events found at {cur_date.format(DATE_FORMAT)}")
    else:
        for event in events_at_date:
            location = event.location
            desc = (event.description or "").strip()[0:200] + '...'
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
                intent = input(f"Log work to {JIRA_ISSUE} (l) or skip (s)?")
                if intent == 'l':
                    worklog = jira_client.add_worklog(JIRA_ISSUE, begin, duration.seconds, name, location, desc)
                    print(f"Logged! {worklog.raw['self']}")
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


def init_jira():
    jira_password = keyring.get_password(JIRA_URL, JIRA_USER)
    if jira_password is None:
        jira_password = getpass.getpass(f"Enter password for {JIRA_URL}, user {JIRA_USER}:")
        jira_client = JiraClient(JIRA_URL, JIRA_USER, jira_password)
        keyring.set_password(JIRA_URL, JIRA_USER, jira_password)
        return jira_client
    jira_client = JiraClient(JIRA_URL, JIRA_USER, jira_password)
    return jira_client


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    run()
