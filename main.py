
from dateutil import parser
from json import loads
import requests

# Constants
token = "Basic OTpzaTNlV2M3b0FwL1pwaVgyaU80L0tvRHg2emNXNnVmM2lOa29YMDFvNU5jPQ=="
activities_url = "https://api.slangapp.com/challenges/v1/activities"
sessions_url = "https://api.slangapp.com/challenges/v1/activities/sessions"

def calculate_users_sessions():
    user_sessions = {}
    users_timeline = {}
    # First get the list of activities.
    activities_resp = requests.get(activities_url, headers={'Content-Type': 'application/json', "Authorization": token})
    assert activities_resp, "Bad response [{}] from sessions url".format(activities_resp.status_code)
    activities_list = loads(activities_resp.content)["activities"]


    for activitie in activities_list:

        # Transform dato to time stamps
        answered_ts = isotots(activitie["answered_at"])
        first_seen_ts = isotots(activitie["first_seen_at"])

        # The user will be created in the list if this one dont exist in the dict
        if activitie["user_id"] in user_sessions:

            # Make a binary search to find if the new activity was perform inside an existing period.
            position = search_user_session(users_timeline[activitie["user_id"]], (first_seen_ts, answered_ts))
            if position[0] == "inside":

                # Original time session
                session_answered_time = user_sessions[activitie["user_id"]][position[1]]["ended_at"]
                session_first_seen_time = user_sessions[activitie["user_id"]][position[1]]["started_at"]
                session_answered_ts = isotots(session_answered_time)
                session_first_seen_ts = isotots(session_first_seen_time)

                # Update set the new older and news date on the period
                new_end_time = session_answered_time
                new_end_ts = answered_ts
                if session_answered_ts < answered_ts:
                    new_end_time = activitie["answered_at"]
                    new_end_ts = session_answered_ts

                new_start_time = session_answered_time
                new_start_ts = session_first_seen_ts
                if session_first_seen_ts > first_seen_ts:
                    new_start_time = activitie["first_seen_at"]
                    new_start_ts = first_seen_ts

                #Set the new values inside the period
                selected_session = user_sessions[activitie["user_id"]][position[1]]
                selected_session["ended_at"] = new_end_time
                selected_session["started_at"] = new_start_time
                selected_session["duration"] = new_end_ts - new_start_ts
                selected_session["activity_ids"].append(activitie["id"]),
                users_timeline[activitie["user_id"]] = [(new_end_ts, new_start_ts)]
            else:
                new_session = {
                    "ended_at": activitie["answered_at"],
                    "started_at": activitie["first_seen_at"],
                    "activity_ids": [activitie["id"]],
                    "duration": answered_ts - first_seen_ts,
                }
                user_sessions[activitie["user_id"]] = user_sessions[activitie["user_id"]][:position[1]] + [new_session] + user_sessions[activitie["user_id"]][position[1]:]

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

    #Push the session list into the enpoint
    session_resp = requests.post(sessions_url, json={"user_sessions": user_sessions}, headers={'Content-Type': 'application/json', "Authorization": token})
    assert session_resp, "Bad response [{}] from sessions url".format(session_resp.status_code)

    print("successfully uploaded")

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
            left = mid + 1
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

def isotots(isostr):
    return parser.parse(isostr).timestamp()

if __name__ == '__main__':
    calculate_users_sessions()
