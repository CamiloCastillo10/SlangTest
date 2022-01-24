# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import requests
from json import loads
from datetime import datetime
from dateutil import tz
token = "Basic OTpzaTNlV2M3b0FwL1pwaVgyaU80L0tvRHg2emNXNnVmM2lOa29YMDFvNU5jPQ=="
activities_url = "https://api.slangapp.com/challenges/v1/activities"
sessions_url = "https://api.slangapp.com/challenges/v1/activities/sessions"

def calculate_users_sessions():
    user_sessions = {}
    users_timeline = {}
    # Use a breakpoint in the code line below to debug your script.
    activities_resp = requests.get(activities_url, headers={'Content-Type': 'application/json', "Authorization": token})
    assert activities_resp, "Bad response [{}] from sessions url".format(activities_resp.status_code)
    activities_list = loads(activities_resp.content)["activities"]
    for activitie in activities_list:
        answered_ts = isotots(activitie["answered_at"])
        first_seen_ts = isotots(activitie["first_seen_at"])
        if activitie["user_id"] in user_sessions :
            position = search_user_session(users_timeline[activitie["user_id"]], (first_seen_ts, answered_ts))
            if position[0] == "inside":
                new_end_time = activitie["answered_at"] if user_sessions[activitie["user_id"]]["ended_at"] < activitie["answered_at"] else user_sessions[activitie["user_id"]]["ended_at"]
                new_start_time = activitie["first_seen_at"] if user_sessions[activitie["user_id"]]["started_at"] < activitie["first_seen_at"] else user_sessions[activitie["user_id"]]["started_at"]
                user_sessions[activitie["user_id"]]["ended_at"] = new_end_time
                user_sessions[activitie["user_id"]]["started_at"] = new_start_time
                user_sessions[activitie["user_id"]]["duration"] = new_start_time
                user_sessions[activitie["user_id"]]["activity_ids"].push(activitie["id"]),
                users_timeline[activitie["user_id"]] = [(new_start_time, new_end_time)]
            else:
                new_session = {
                    "ended_at": activitie["answered_at"],
                    "started_at": activitie["first_seen_at"],
                    "activity_ids": [activitie["id"]],
                    "duration": answered_ts - first_seen_ts,
                }
                user_sessions[activitie["user_id"]] = user_sessions[activitie["user_id"]][:position[1]] + new_session + user_sessions[activitie["user_id"]][position[1]:]

        else:
            user_sessions[activitie["user_id"]] = [
                {
                    "ended_at": activitie["answered_at"],
                    "started_at": activitie["first_seen_at"],
                    "activity_ids": [activitie["id"]],
                    "duration": answered_ts - first_seen_ts,
                }
            ]
            users_timeline[activitie["user_id"]] = [(first_seen_ts, answered_ts)]


    session_resp = requests.post(sessions_url, json={"user_session": user_sessions}, headers={'Content-Type': 'application/json', "Authorization": token})
    assert session_resp, "Bad response [{}] from sessions url".format(session_resp.status_code)

    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.

def search_user_session(session_timeline, activity_period):
    left = 0
    right = len(session_timeline) - 1
    while left <= right:
        mid = (left + right) // 2
        position = is_period_outside_session(session_timeline[mid], activity_period)
        if position == "inside":
            return position, mid
        elif position == "left":
            right = mid - 1
        else:
            left + 1
    return position, mid

def is_period_outside_session(session_period, activity_period):
    ret = "inside"
    is_outside_left = session_period[0] > activity_period[1] + 500
    is_outside_right = session_period[1] + 500 < activity_period[0]
    if is_outside_left and not is_outside_right:
        ret = "left"
    elif not is_outside_left and is_outside_right:
        ret = "right"
    return ret

def isotots(isostr, fmt='%Y-%m-%dT%H:%M:%S.%fZ'):
    return datetime.strptime(isostr, fmt).replace(tzinfo=tz.tzutc()).timestamp()

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    calculate_users_sessions()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
