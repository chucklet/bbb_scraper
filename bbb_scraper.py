import requests
import datetime
import json
import calendar
from googlevoice import Voice

# This program logs in and retrieves all current schedule data from BBB JDA webserver,
# then formats it, and sends it to a phone via Google Voice SMS.
# By Charles Martin

# Global Variables/Config Values
MAX_TEXT_LENGTH = 150
PHONE_NUMBER = "+1FOOBAR" #+1 (Country Code) and then 10-digit phone number, no separators
BBB_USERNAME = "YOUR USER NAME"
BBB_PASSWORD = "YOUR PASSWORD"

login_data = {'loginName': BBB_USERNAME, 'password': BBB_PASSWORD}

today = datetime.date.today()
s = requests.session()

# This function gets JSON schedule data from JDA for the week of a given date, and returns it as a python dict.
def getSchedule(wantedDate):
    r = s.get('https://bbnb-wfmr.jdadelivers.com/retail/data/ess/api/MySchedule/' + str(today) + '?&id=' +
              str(wantedDate) + '&siteId=1001414')  # Get schedule for this week from JDA API
    return json.loads(r.text)  # And return it as a dictionary

# This function extracts all known workdays from JDA, cleans them, and makes a list of them.
def buildShiftList():
    finishedShiftList = []
    wantedDate = today
    webSchedule = getSchedule(today)  # get this weeks schedule
    while (webSchedule["data"]["NetScheduledHours"]):  # Keep going until no hours for the week
        for day in webSchedule["data"]["Days"]:
            for shift in day['PayScheduledShifts']:
                finishedShiftList.append({ #This is all I need to keep from each shift
                    'id' : shift['ScheduledShiftID']+1,
                    'job' : shift['Job']['Name'],
                    'start' : shift['Start'],
                    'end' : shift ['End']
                })
        wantedDate += datetime.timedelta(days=7)  # go to next week
        webSchedule = getSchedule(wantedDate)  # get next week, repeat
    return finishedShiftList  # returns all scheduled days from this week and every week after
                              # until there is a completely unscheduled week

def makePretty(shift):
    shiftDay = datetime.datetime.strptime(shift['start'][:10], "%Y-%m-%d")
    return    calendar.day_name[shiftDay.weekday()][:3] + " " + shift['start'][5:10] + ": " + shift['start'][11:16] + " to " + shift['end'][11:16] + "\n"

def sendText(words):
    voice = Voice()
    voice.login()
    voice.send_sms(PHONE_NUMBER, words)

def main():
    s.post('https://bbnb-wfmr.jdadelivers.com/retail/data/login', login_data)  # Log in
    shifts = buildShiftList()

    msgBody = ""
    for shift in shifts:
        shiftStr = makePretty(shift)
        if len(msgBody) + len(shiftStr) <= MAX_TEXT_LENGTH: # If shift fits in current message, add it
            msgBody += shiftStr 
        else: # Else send message and start a new one
            sendText(msgBody[:-1]) # -1 gets rid of newline at the end
            msgBody = shiftStr
    sendText(msgBody[:-1])

main()
