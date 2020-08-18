import getpass
import logging
import os
from datetime import date

import arrow
import dateutil
import keyring
import requests
from arrow import Arrow
from ics import Calendar as icsCalendar, Event, Calendar
from ics.grammar.parse import Container, ContentLine

from jiraClient import JiraClient

# TODO: Externalize
JIRA_URL = "https://jira.crpt.ru/"
JIRA_USER = "d.sulimchuk"
PROJECT = "MDLP"
DATE_FORMAT = 'YYYY-MM-DD'
JIRA_ISSUE = "MDLP-13463"
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


def get_recurring_rule(extra: Container) -> ContentLine:
    for x in extra:
        if x.name == "RRULE":
            return x
    return None


class LocalEvent:
    begin: Arrow

    def __init__(self, event: Event, overridden_date: Arrow = None):
        self.location = event.location
        self.desc = (event.description or "").strip()[0:200] + '...'
        self.name = event.name
        self.begin = overridden_date or event.begin
        self.duration = event.duration


def generate_local_event_from_rr(le: Event, cur_date: date):
    recurring_rule = get_recurring_rule(le.extra).value
    rule = dateutil.rrule.rrulestr(recurring_rule, dtstart=le.begin.datetime)
    # print(rule)
    for d in rule:
        # print(d.date())
        if d.date() == cur_date:
            return LocalEvent(le, arrow.get(d))


def find_recurring_events(calendar: Calendar, cur_date: date):
    recurring_events = []
    for e in calendar.events:
        if get_recurring_rule(e.extra):
            local_event = generate_local_event_from_rr(e, cur_date)
            if local_event:
                recurring_events.append(local_event)
    return recurring_events


def run():
    jira_client = init_jira()
    raw_calendar = download_calendar()
    calendar = icsCalendar(raw_calendar)
    print(f"Loaded {len(calendar.events)} events")
    cur_date = ask_date()
    events_at_date = [LocalEvent(e) for e in calendar.events if e.begin.date() == cur_date.date()]
    recurring_events = find_recurring_events(calendar, cur_date.date())
    all_events = (events_at_date + recurring_events)
    all_events.sort(key=lambda x: x.begin)
    if len(all_events) == 0:
        print(f"No events found at {cur_date.format(DATE_FORMAT)}")
    else:
        for e in all_events:
            cls()
            print("##################################################################################")
            print(f"Event: {e.name}")
            print(f"Date: {e.begin.naive}")
            print(f"Duration: {e.duration}")
            print(f"Description: {e.desc}")
            while True:
                intent = input(f"Log work to {JIRA_ISSUE} (l) or skip (s)?")
                if intent == 'l':
                    worklog = jira_client.add_worklog(JIRA_ISSUE, e.begin, e.duration.seconds, e.name, e.location,
                                                      e.desc)
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
