# Required imports
import os
import numpy as np
import json
import requests
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
from google.cloud.firestore import GeoPoint
from random import randrange
import placement

TILES_PER_FIELD_X = 8
TILES_PER_FIELD_Y = 8
MAX_HEIGHT_LEVELS = 4

ELEVATION_ENDPOINT = "http://34.174.221.76"

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
fields = db.collection('fields_test')
usersCollection = db.collection('users')
gatesCollection = db.collection("gates_test")
ivCollection = db.collection('rpi_gates')

# Grabbed this from Geeks4Geeks because I don't need to write this myself
def closest(lst, K):
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))]

#the addField and addGate routes will not work until the user signs in(sign in route)
@app.route("/",methods = ['GET'])
def start():
     return jsonify({"success": True}), 200



















@app.route("/updateNodeIds", methods = ["GET","POST"])
def updateNodeId():
    try:
        jsonRequest = request.get_json()
        gates = set(jsonRequest.keys())
        print(gates)
        docs = db.collection(u'gates_test').stream() 

        for doc in docs:
            currentGateId = str(doc.id)
            if currentGateId in gates:
                nodeID = jsonRequest[currentGateId]
                updatedFieldsDocument ={
                    "node_id":nodeID,
                }
                gatesCollection.document(doc.id).update(updatedFieldsDocument)                

        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"


@app.route("/signup", methods =['GET','POST'])
def signUp():
    try:
        newUserId = request.get_json()['userID']
        jsonEntry = {
            'first_name': 'Jose',
            'last_name':'Martinez',
            'fields':[]
        }
        usersCollection.document(newUserId).set(jsonEntry)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

@app.route("/signin", methods =['GET','POST'])
def signIn():
    global currentUserReference
    currentUser = request.get_json()['userID']
    currentUserReference = f"users/'{currentUser}'"
    print("currentUser",currentUserReference)
    return jsonify({"success": True}), 200

#sample request_body
# {
#     "geopoint_1": "30|50",
#     "geopoint_2": "30|60",
#     "geopoint_3": "30|70",
#     "geopoint_4": "30|80"
# }

#GET - ID
#POST - FIELD
@app.route("/addField", methods =['GET','POST'])
def addField():
    try:
        firstGeopoint = request.get_json()['nw']
        secondGeopoint = request.get_json()['ne']
        thirdGeopoint = request.get_json()['sw']
        fourthGeopoint = request.get_json()['se']

        #creating fields and doc object to generate a fieldID
        fieldEntry = fields.document()        
        docJsonEntry = {
            "user_id": 3,
            "field_name":'test_field',
            "nw_point" : firstGeopoint,
            "ne_point": secondGeopoint,
            "sw_point": thirdGeopoint,
            "se_point": fourthGeopoint,
            "gates":[]
        }
        fieldEntry.set(docJsonEntry)
        return jsonify({"success": fieldEntry.get().id})
    except Exception as e:
        return f"An Error Occurred: {e}"

@app.route("/getFields",methods = ['GET','POST'])
def getFields():
    try:
        userFields = fields.where('user_id',u'==',str(db.document(currentUserReference).id)).get()
        jsonResponse ={}

        for field in userFields:
            doc = field.to_dict()
            jsonResponse[field.id] = {
                'first_geopoint':str(doc['first_point'].latitude) + "|" + str(doc['first_point'].longitude),
                'second_point': str(doc['second_point'].latitude) + "|" + str(doc['second_point'].longitude),
                'third_point': str(doc['third_point'].latitude) + "|" + str(doc['third_point'].longitude),
                'fourth_point': str(doc['fourth_point'].latitude) + "|" + str(doc['fourth_point'].longitude),
            }
        return jsonResponse
    except Exception as e:
        return f"An Error Occurred: {e}"


    


#sample request body
# {
#     "field_id": "yWezzFDhrspN5lAf52Jo",
#     "location": "50|50"
# }

@app.route("/editGate",methods =['GET','POST'])
def editGate():
    json = request.get_json()
    global gates
    gates = []
    jsonResponse = {}
    gates = ivCollection.stream()



    for gate in gates:
        currentGate = gate.to_dict()
        if "node_id" not in currentGate.keys():

            updatedFieldsDocument = {
                "node_id":gates[0],
                "location": str(currentGate["location"].latitude) + "|"  + str(currentGate["location"].longitude),
                "gate_height": currentGate["gate_height"]          
            }
            ivCollection.document(gate.id).update(updatedFieldsDocument)

@app.route("/setGateHeight", methods =['GET','POST'])
def setGates():
    json = request.get_json()

    gateHeight = request.get_json()['height']
    print(gateHeight)
    gates = gatesCollection.stream()
    jsonResponse = {}

    for gate in gates:
        currentGate = gate.to_dict()
        jsonResponse[gate.id] = {
            "location": str(currentGate["location"].latitude) + "|"  + str(currentGate["location"].longitude),
            "gate_height": currentGate["gate_height"],
            "node_id": 0,       
        }
    return jsonResponse

    # return jsonify({"success": True}), 200





    # gates = ivCollection.stream()

    # for gate in gates:
    #     currentGate = gate.to_dict()
    #     if "node_id" not in currentGate.keys():
    #         updatedFieldsDocument = {
    #             "node_id":gates[0],
    #             "location": str(currentGate["location"].latitude) + "|"  + str(currentGate["location"].longitude),
    #             "gate_height": currentGate["gate_height"]          
    #         }
    #         ivCollection.document(gate.id).update(updatedFieldsDocument)





    # #loop through all gates in Database and add in Node_Ids from json. Account for mismatch sizes
    # for gate in json.values():
    #     gates.append(gate)

    return json


@app.route("/addGate", methods =['GET','POST'])
def addGates():
    try:
        
        fieldID  = request.get_json()["field_id"]
        gateLocation = request.get_json()["gateLocation"]
        gateEntry = gatesCollection.document()        

        gateJson = {
            "field_id":fieldID,
            "location":gateLocation,
            "gate_height": 75,
            "node_id":-1
        }
        gateEntry.set(gateJson)
        return jsonify({"success": True})
    except Exception as e:
        return f"An Error Occurred: {e}"

#end point for retreving gates - must take a fieldID
@app.route("/getGates",methods = ['GET','POST'])
def fetchGates():
    try:
        #getting field collection containg gates
        # fieldID = request.get_json()["field_id"]
        # field = fields.document(str(fieldID)).get().to_dict()
        # gateIDs = field["gates"]
        jsonResponse = {}


        gates = gatesCollection.stream()

        for gate in gates:
            currentGate = gate.to_dict()
            jsonResponse[gate.id] = {
                "lat": currentGate["lat"],
                "long":currentGate["long"],
                "gate_height": currentGate["gate_height"],
                "node_id":currentGate["node_id"],         
            }

        # # #getting gates
        # for gate in gateIDs:
        #     currentGate = gatesCollection.document(str(gate)).get().to_dict()
        #     jsonResponse[gate] = {
        #         "location": str(currentGate["location"].latitude) + "|"  + str(currentGate["location"].longitude),
        #         "gate_height": currentGate["gate_height"]
        #     }
        print('RESPONSE BEING RETURNED',jsonResponse)
        return jsonResponse
    except Exception as e:
        return f"An Error Occurred: {e}"
    
@app.route('/getField', methods=['GET','POST'])
def getField():
    try:
        gateID = request.get_json()["fieldID"]
        jsonResponse = fields.document(gateID).get().to_dict()
        return jsonResponse
    except Exception as e:
        return f"An Error Occurred: {e}"

@app.route('/tile-field',methods=['GET', 'POST'])
def tileField():
	# get the field boundaries using field_id and endpoint

    current_field = {}

    try:
        gateID = request.get_json()["fieldID"]
        jsonResponse = fields.document(gateID).get().to_dict()
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
  
@app.route('/add', methods=['POST'])
def create():
    """
        create() : Add document to Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'id': '1', 'title': 'Write a blog post'}
    """
    try:
        id = request.json['id']
        todo_ref.document(id).set(request.json)
        print("help")
        return jsonify({"success": True}), 201
    except Exception as e:
        return f"An Error Occurred: {e}"

@app.route('/list', methods=['GET'])
def read():
    """
        read() : Fetches documents from Firestore collection as JSON.
        todo : Return document that matches query ID.
        all_todos : Return all documents.
    """
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

@app.route('/update', methods=['POST', 'PUT'])
def update():
    """
        update() : Update document in Firestore collection with request body.
        Ensure you pass a custom ID as part of json body in post request,
        e.g. json={'id': '1', 'title': 'Write a blog post today'}
    """
    try:
        id = request.json['id']
        todo_ref.document(id).update(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

@app.route('/delete', methods=['GET', 'DELETE'])
def delete():
    """
        delete() : Delete a document from Firestore collection.
    """
    try:
        # Check for ID in URL query
        todo_id = request.args.get('id')
        todo_ref.document(todo_id).delete()
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occurred: {e}"

@app.route('/gates', methods=['GET'])
def placeGates():
    try:
        print("trying to place gates")
        gateplacements = placement.generateGatePlacement(0, 0, np.empty([2, 2])).tolist()
        # print(json.dumps(gateplacements))
        return jsonify(json.dumps(gateplacements)), 200
    except Exception as e:
        return f"An Error Occurred: {e}"
        

port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)


#end point -> 4 latitude points 



#another route within a field
#add another titles property into fields that 
#1.title ID
#2.4 verticies
#3.relative height