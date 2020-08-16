from jira import JIRA


class JiraClient:
    seconds_in_hour = 3600

    def __init__(self, url, login, password) -> None:
        self.jira = JIRA(url, auth=(login, password))

    def add_worklog(self, issue, work_date, duration_seconds, name, location, description):
        return self.jira.add_worklog(
            issue,
            timeSpentSeconds=duration_seconds,
            started=work_date,
            comment=f"*AUTO FROM CALENDAR*\n*Event:* {name}\n*Location:* {location}\n*Description:* {description}"
        )

