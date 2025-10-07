from flask import Flask
import pymongo
from bson import json_util
import os
from dotenv import load_dotenv 
from datetime import date

app = Flask(__name__)
load_dotenv()

# initialize environment variable
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')

# set up PyMongo Client
client = pymongo.MongoClient(app.config['MONGO_URI'], server_api=pymongo.server_api.ServerApi('1'))

# define mongo variables
db = client['eventsDB']
calendar = db['calendar']

# map semesters to the corresponding months
semester_map = {
    "S": ['01', '02', '03', '04'],
    "A": ['05', '06', '07', '08'],
    "F": ['09', '10', '11', '12']
}

# finds the semester we're currently in
def get_current_semester():
    year = str(date.today().year)
    year = year[2:]

    semester = ""
    month = str(date.today().month)
    for x in semester_map.keys():
        if month in semester_map[x]:
            semester = x
            break
    
            
    return semester + year

def get_semester(identifier):
    # ensure the identifier is the right length and starts with a real semester, otherwise get current semester
    if (len(identifier) != 3):
        identifier = get_current_semester()
    if (identifier[0] not in semester_map.keys()):
        identifier = get_current_semester()
    # ensure that the year is formatted correctly, or get current semester, and then separate the year out
    try:
        int(identifier[1:])
    except:
        identifier = get_current_semester()
    
    # seperate out the semester identifier
    semester = identifier[0]
    # get the year component
    year = identifier[1:]

    date_strings = ['20' + year + '-' + x for x in semester_map[semester]]
    return date_strings

#returns a JSON response with the format {data : [array of relevant events]} 
def query_calendar(id):
    # get relevant data
    date_strings = get_semester(id)
    events = calendar.find()

    # create a calendar to jsonify
    jdict = {"data" : []}

    # find qualifying events
    for event in events:
        event_date =str(event["date"])[:7]
        if event_date in date_strings:
            event["_id"] = str(event["_id"]) # convert ObjectId to string for better jsonify
            jdict["data"].append(event)
    
    return json_util.dumps(jdict)

def main(id):
    return query_calendar(id)