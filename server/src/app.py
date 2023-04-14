# Required imports
import os
import numpy as np
import asyncio
import json
import requests
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app, auth, _auth_utils
from google.cloud.firestore import GeoPoint
from weather_api import requestWeather

from random import randrange
import placement

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

# Initialize Flask app
app = Flask(__name__)

# Initialize Firestore DB
cred = credentials.Certificate('key.json')
default_app = initialize_app(cred)
db = firestore.client()

#Initializing Collections
todo_ref = db.collection('todos')
fields = db.collection('fields')
usersCollection = db.collection('users')
gatesCollection = db.collection("gates_test")
realGatesCollection = db.collection('gates')
currentUserReference = None

TILES_PER_FIELD_X = 8
TILES_PER_FIELD_Y = 8


MAX_HEIGHT_LEVELS = 4

ELEVATION_ENDPOINT = "http://34.174.221.76"

#main link: https://todo-proukhgi3a-uc.a.run.app
# Grabbed this from Geeks4Geeks because I don't need to write this myself
def closest(lst, K):
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))]

def check_auth(token: str):
    try:
        print("token!!",token)

        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']

        print("Decoded token = ", end="")
        print(decoded_token)
        return True,uid
    except _auth_utils.InvalidIdTokenError:
        print("INVALID ID TOKEN")

        return False, ""

def updateFieldDocument(fieldID,gateID):
    try:
        fieldDocument = fields.document(fieldID)
        fieldDocument.update({u'gates': firestore.ArrayUnion([str(gateID)])})
        jsonResponse = fields.document(fieldID).get().to_dict()
        return jsonResponse
    except Exception as e:
        return f"An Error Occurred: {e}"

def initializeUser(userID):
    print("user",userID)
    initialEntry = {
        "fields":[],
        "todos":[]
    }
    usersCollection.document(str(userID)).set(initialEntry)

def updateFieldUser(fieldID,userID):
    usersDocument = usersCollection.document(userID)
    usersDocument.update({u'fields': firestore.ArrayUnion([str(fieldID)])})

def updateTodoUser(user_id,todo_id):
    usersDocument = usersCollection.document(user_id)
    usersDocument.update({u'todos': firestore.ArrayUnion([str(todo_id)])})


#the addField and addGate routes will not work until the user signs in(sign in route)
@app.route("/",methods = ['GET'])
def start():
     return jsonify({"success": True})

@app.route("/weather_forecast/<lat>/<long>", methods = ['GET'])
def getWeather(lat = 0.0, long=0.0):
    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):
        try:
            forecast_data = requestWeather(lat, long)#(36.082157, -94.171852)
            forecast_hourly = forecast_data['hourly']
            #print(forecast_hourly.keys())
            #print(forecast_data['hourly']) 
            return jsonify({"precipitation_hourly": forecast_hourly['precipitation'], "timedate_hourly": forecast_hourly['time']}), 200
        except:
            return jsonify(({"error":"error occured with weather api"})), 500
    else:
        return ("FORBIDDEN", 403)


# sampleRequestBody - key:gateID value:newNodeId
# {
#   "XpRSItWlLGa1b4NuDvJn" : "10"a
# }
@app.route("/updateNodeIds", methods = ["GET","POST"])
def updateNodeId():
    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):
        try:
            jsonRequest = request.get_json()
            gates = set(jsonRequest.keys())
            docs = db.collection(u'gates').stream()
            print(gates)

            for doc in docs:
                currentGateId = str(doc.id)
                if currentGateId in gates:
                    nodeID = jsonRequest[currentGateId]
                    updatedFieldsDocument ={
                        "nodeID":nodeID,
                    }
                    realGatesCollection.document(doc.id).update(updatedFieldsDocument)                
            return jsonify({"success": True}), 200
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)

@app.route("/deleteField",methods = ['GET','POST'])
def deleteField():
    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):
        try:
            fieldID = request.get_json()['fieldID']
            fields.document(fieldID).delete() 
            return jsonify({"success": True}), 200
        except Exception as e:
            return f"An Error Occurred : {e}"
    else:
        return ("FORBIDDEN", 403)


#sample request
# {
#     "auth_token":
# }
@app.route("/signup", methods =['GET','POST'])
def signUp():
    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]
    if (check_auth(auth_token)[0]):
        initializeUser(check_auth(auth_token)[1])
        return jsonify({"success": True}), 200
    else:
        return ("FORBIDDEN", 403)


#may not beed needed
@app.route("/signin", methods =['GET','POST'])
def signIn():
    auth_token = request.json()["token"]
    if (check_auth(auth_token)[0]):
        currentUser = check_auth(auth_token)[1]
        activeUser = {
            "activeUser":"true"
        }
        usersCollection.document(currentUser).update(activeUser)
        return jsonify({"success": True}), 200
    else:
        return ("FORBIDDEN", 403)

#may also not be needed
@app.route("/signout",methods = ['GET','POST'])
def signout():
    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]
    if (check_auth(auth_token)[0]):
        try:
            userID = request.get_json()['userID']
            jsonEntry = {
                "activeUser":'false'
            }
            usersCollection.document(userID).update(jsonEntry)
            return jsonify({"success":True}),200
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)

#sample requestBody
# {
#     "nw":"36.0627|-94.1606",
#     "ne": "36.0628|-94.1606",
#     "sw": "36.0628|-94.1605",
#     "se": "36.0627|-94.1605"
# }
@app.route("/addField", methods =['GET','POST'])
def addField():
    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"] 
    if (check_auth(auth_token)[0]):
        try:
            firstGeopoint = request.get_json()['nw']
            secondGeopoint = request.get_json()['ne']
            thirdGeopoint = request.get_json()['sw']
            fourthGeopoint = request.get_json()['se']

            #creating fields and doc object to generate a fieldID
            fieldEntry = fields.document()        
            docJsonEntry = {
                "field_name":'test_field',
                "nw_point" : firstGeopoint,
                "ne_point": secondGeopoint,
                "sw_point": thirdGeopoint,
                "se_point": fourthGeopoint,
                "gates": []
            }
            fieldEntry.set(docJsonEntry)
            fieldID = fieldEntry.id
            return jsonify({"success": fieldID}), 200

            # user = check_auth(auth_token)[1]
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)


#sample request
# {
#     "height":"10",
#     "gateID":"3dOtNkbfYAKpVSmHYNu5"
# }
@app.route("/setGateHeight", methods =['GET','POST'])
def setGateHeight():

    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):
        try:
            gateHeight = request.get_json()['height']
            gateID = request.get_json()['gateID']

            updatedGateDocument = {"height":gateHeight}
            realGatesCollection.document(gateID).update(updatedGateDocument)

            return jsonify({"success": True}), 200
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)

#sample request body - when we have fieldID

# {
#     "gateLocation":"30|50",
#     "fieldID":"1jI2LDfXbikCODe2IEEm"
# }
#sample request body-no fieldID-use this one
# {
#     "gateLocation":"30|50",
# }
@app.route("/addGate", methods =['GET','POST'])
def addGates():

    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):
        try:
            gateEntry = realGatesCollection.document()

            lat,long = tuple(request.get_json()["gateLocation"].split("|"))
            fieldID = request.get_json()["fieldID"]

            gateJson = {
                "lat": lat,
                "long":long,
                "nodeID":0,
                "height":20
            }
            gateEntry.set(gateJson)
            createdGateID = gateEntry.id
            updateFieldDocument(fieldID,createdGateID)
            return jsonify({"success": True})
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:   
        return ("FORBIDDEN", 403)

@app.route("/getGates",methods = ['GET','POST'])
def fetchGates():

    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):
        try:
            jsonResponse = {}

            gates = realGatesCollection.stream()
            for gate in gates:
                currentGate = gate.to_dict()
                jsonResponse[gate.id] = {
                    "lat": currentGate["lat"],
                    "long":currentGate["long"],
                    "height": currentGate["height"],
                    "nodeID":currentGate["nodeID"]         
                }
            return jsonResponse
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)
    
@app.route('/getField', methods=['GET','POST'])
def getField():
    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):

        try:
            gateID = request.get_json()["fieldID"]
            jsonResponse = fields.document(gateID).get().to_dict()
            return jsonResponse
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403) 


@app.route('/getFields', methods=['GET','POST'])
def getFields():
    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]   
    if (check_auth(auth_token)[0]):
        fieldResponse = []
        try:
            fields = fields.stream()
            for field in fields:
                fieldResponse.append(field.id)
            # user = check_auth(auth_token)[1]
            # fields = usersCollection.document(str(user)).get().to_dict()["fields"]
            
            jsonResponse = json.dumps(fieldResponse)

            return jsonResponse
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)


#sample request body
# {
#     "gateID":"5bVRcE4HoyhO9JnAXG1w",
#     "location":"50|40"
# }
@app.route('/adjustGateLocation', methods=['GET','POST'])
def adjustGateLocation():

    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):
        try:
            lat,long = tuple(request.get_json()["location"].split("|"))
            gateID = request.get_json()['gateID']
            updatedGateDocument = {
                "lat":lat,
                "long":long
            }
            realGatesCollection.document(gateID).update(updatedGateDocument)        
            return jsonify({"success": True})
        except Exception as e:
            return f"An Error Occurred: {e}"
    
    else:
        return ("FORBIDDEN", 403)

#sample request
# {
#     "fieldID":"1jI2LDfXbikCODe2IEEm"
# }
@app.route('/tile-field',methods=['GET', 'POST'])
def tileField():

    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):

        current_field = {}
        try:
            gateID = request.get_json()["fieldID"]
            jsonResponse = fields.document(gateID).get().to_dict()
            print("JSON",jsonResponse)
            current_field = jsonResponse.copy()
        except Exception as e:
            return f"An Error Occurred: {e}"
        
        test_field : dict[str, str] = {
            'sw_point': "36.0627|-94.1606",
            'nw_point': "36.0628|-94.1606",
            'ne_point': "36.0628|-94.1605",
            'se_point': "36.0627|-94.1605"
        }

        ########################

        #current_field : dict[str, str] = test_field.copy()

        trans_field : dict[str: [str, float]] = {
            "sw_point" : {
                "lat" : float(current_field["sw_point"].split('|')[0]),
                "long" : float(current_field["sw_point"].split('|')[1])
            }, 
            "nw_point" : {
                "lat" : float(current_field["nw_point"].split('|')[0]),
                "long" : float(current_field["nw_point"].split('|')[1])
            }, 
            "se_point" : {
                "lat" : float(current_field["se_point"].split('|')[0]),
                "long" : float(current_field["se_point"].split('|')[1])
            }, 
            "ne_point" : {
                "lat" : float(current_field["ne_point"].split('|')[0]),
                "long" : float(current_field["ne_point"].split('|')[1])
            }
        } 
        
        print(trans_field)
        
        # tile the field and get the width and height of each tile

        n_dist = abs(trans_field["ne_point"]["long"] - trans_field["nw_point"]["long"])
        s_dist = abs(trans_field["se_point"]["long"] - trans_field["sw_point"]["long"])
        e_dist = abs(trans_field["se_point"]["lat"] - trans_field["ne_point"]["lat"])
        w_dist = abs(trans_field["sw_point"]["lat"] - trans_field["nw_point"]["lat"])

        print("n_dist = " + str(n_dist))
        print("s_dist = " + str(s_dist))
        print("w_dist = " + str(w_dist))
        print("e_dist = " + str(e_dist))

        tile_width = ((n_dist + s_dist) / 2) / TILES_PER_FIELD_X
        tile_height = ((e_dist + w_dist) / 2) / TILES_PER_FIELD_Y

        print("tile_widt = " + str(tile_width))
        print("tile_height = " + str(tile_height))

        print("BELOW THIS IS THE TILES_DICT \n")

        tiles_dict: dict[int: [str, str]] = {}

        for i in range(TILES_PER_FIELD_Y):
            for j in range(TILES_PER_FIELD_X):
                tile_dict = {}

                tile_dict["sw_point"] = str(trans_field["sw_point"]["lat"] + i*tile_height) + \
                "|" + \
                str(trans_field["sw_point"]["long"] + (j*tile_width))

                tile_dict["nw_point"] = str(trans_field["sw_point"]["lat"] + (i*tile_height + tile_height)) + \
                "|" + \
                str(trans_field["sw_point"]["long"] + (j*tile_width))

                tile_dict["se_point"] = str(trans_field["sw_point"]["lat"] + (i*tile_height)) + \
                "|" + \
                str(trans_field["sw_point"]["long"] + (j*tile_width + tile_width))

                tile_dict["ne_point"] = str(trans_field["sw_point"]["lat"] + (i*tile_height + tile_height)) + \
                "|" + \
                str(trans_field["sw_point"]["long"] + (j*tile_width + tile_width))
                
                tiles_dict[i*TILES_PER_FIELD_X + j] = tile_dict

        print(tiles_dict)

        # go get heights of every tile in dict and add to tiles_dict

        for i in range(TILES_PER_FIELD_X * TILES_PER_FIELD_Y):
            
            url = ELEVATION_ENDPOINT + "/api/v1/lookup?locations=" + \
            tiles_dict[i]["sw_point"].split('|')[0] + "," + \
            tiles_dict[i]["sw_point"].split('|')[1]

            print("url_test = " + url)

            response = requests.get(url)

            if (response.status_code == 200):
                data = {}
                data = response.json()

                print(data)

                tiles_dict[i]["elevation"] = data['results'][0]['elevation']

        print("tiles post elevation... \n")
        print(tiles_dict)

        # normalize heights

        height_set : set = set([])

        for tile in tiles_dict:
            height_set.add(tiles_dict[tile]["elevation"])

        print("height set = ", str(height_set))

        while (len(height_set) > MAX_HEIGHT_LEVELS):
            first_val = height_set.pop()
            sec_val = height_set.pop()

            height_set.add((sec_val + first_val) / 2)

        # build json response object of tiles

        for tile in tiles_dict:
            closest_val = closest(list(height_set), tiles_dict[tile]["elevation"])
            tiles_dict[tile]["height_val"] = list(height_set).index(closest_val)
        
        print("FINAL TILES DICT = \n\n\n")
        print(tiles_dict)

        print("VISUAL\n\n")
        print("this is", end="")
        print(" a test")

        for i in range(TILES_PER_FIELD_Y):
            for j in range(TILES_PER_FIELD_X):
                if (tiles_dict[i*TILES_PER_FIELD_X +j]["height_val"] == 0): 
                    print("\033[1;32mO", end="")
                elif (tiles_dict[i*TILES_PER_FIELD_X +j]["height_val"] == 1):
                    print("\033[1;33mO", end="")
                else:
                    print("\033[1;34mO", end="")
            print("")

        print("\033[0m\nEND OF TEST")

        return jsonify(tiles_dict)
    
    else:
        return ("FORBIDDEN", 403)

@app.route('/add', methods=['POST'])
def create():
    """
        create() : Add document to Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'id': '1', 'title': 'Write a blog post,}
    """
    # currentUser = getActiveUser()
    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):  
        try:
            userID =auth_token[1]
            newToDo = todo_ref.document()
            newToDo.set(request.json)
            updateTodoUser(userID,newToDo.id)
            print("help")
            return jsonify({"success": True})
        except Exception as e:
            print(e)
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)

@app.route('/list', methods=['GET'])
def read():
    """
        read() : Fetches documents from Firestore collection as JSON.
        todo : Return document that matches query ID.
        all_todos : Return all documents.
    """
    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]
    if (check_auth(auth_token)[0]):  
        try:
            # Check if ID was passed to URL query
            todo_id = request.args.get('id')
            if todo_id:
                todo = todo_ref.document(todo_id).get()
                return jsonify(todo.to_dict()), 200
            else:
                all_todos = [doc.to_dict() for doc in todo_ref.stream()]
                return jsonify(all_todos), 200
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)

@app.route('/update', methods=['POST', 'PUT'])
def update():
    """
        update() : Update document in Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'id': '1', 'title': 'Write a blog post today'}
    """

    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):

        try:
            id = request.json['id']
            todo_ref.document(id).update(request.json)
            return jsonify({"success": True}), 200
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)

@app.route('/delete', methods=['GET', 'DELETE'])
def delete():
    """
        delete() : Delete a document from Firestore collection.
    """

    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):
        try:
            # Check for ID in URL query
            todo_id = request.args.get('id')
            todo_ref.document(todo_id).delete()
            return jsonify({"success": True}), 200
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)

@app.route('/gates', methods=['GET'])
def placeGates():

    auth_token = (False, "")
    try: 
        auth_token = request.headers.get('Authorization')
    except KeyError:
        auth_token = request.get_json()["auth_token"]

    if (check_auth(auth_token)[0]):
        try:
            print("trying to place gates")
            gateplacements = placement.generateGatePlacement(0, 0, np.empty([2, 2])).tolist()
            # print(json.dumps(gateplacements))
            return jsonify(json.dumps(gateplacements)), 200
        except Exception as e:
            return f"An Error Occurred: {e}"
    return ("FORBIDDEN", 403)
        

port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)


#end point -> 4 latitude points 

#another route within a field
#add another titles property into fields that 
#1.title ID
#2.4 verticies
#3.relative height