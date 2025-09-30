from flask import Flask
import pymongo
from dotenv import load_dotenv
import os
from get_shoot import get_shoot

load_dotenv()

# Initialize flask application
app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv("MONGO_URI")
client = pymongo.MongoClient(app.config['MONGO_URI'])

# Initialize databases
eventsDB = client['eventsDB']
shoots = eventsDB['shoot']
events = eventsDB['event']

# Routes
@app.route("/api/shoot/<shoot_id>", methods=["GET"])
def get_shoot_route(shoot_id):
    return get_shoot(shoots, shoot_id)

if __name__ == "__main__":
    app.run(debug=True)
