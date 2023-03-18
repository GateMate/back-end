# Required imports
import os
import numpy as np
import json
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
from google.cloud.firestore import GeoPoint
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
fields = db.collection('fields_test')
usersCollection = db.collection('users')
gatesCollection = db.collection("gates_test")
ivCollection = db.collection('rpi_gates')



#the addField and addGate routes will not work until the user signs in(sign in route)
@app.route("/",methods = ['GET'])
def start():
     return jsonify({"success": True}), 200

@app.route("/updateNodeIds", methods = ["GET","POST"])
def updateNodeId():
    try:
        jsonRequest = request.get_json()
        gates = gatesCollection.stream()
        for gate in gates:
            currentGateId = gate.id
            nodeID = jsonRequest[currentGateId]
            updatedFieldsDocument ={
                "node_id":nodeID,
            }
            gatesCollection.document(gate.id).update(updatedFieldsDocument)
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
@app.route("/addField", methods =['GET','POST'])
def addField():
    try:
        lat,lng = (tuple([float(x) for x in request.get_json()['geopoint_1'].split("|")]))
        firstGeopoint = GeoPoint(lat,lng)

        lat,lng = (tuple([float(x) for x in request.get_json()['geopoint_2'].split("|")]))
        secondGeopoint = GeoPoint(lat,lng)
        
        lat,lng = (tuple([float(x) for x in request.get_json()['geopoint_3'].split("|")]))
        thirdGeopoint = GeoPoint(lat,lng)

        lat,lng = (tuple([float(x) for x in request.get_json()['geopoint_4'].split("|")]))
        fourthGeopoint = GeoPoint(lat,lng)


        #creating fields and doc object to generate a fieldID
        fieldEntry = fields.document()        
        docJsonEntry = {
            "user_id": db.document(currentUserReference).id,
            "field_name":'test_field',
            "first_point" : firstGeopoint,
            "second_point": secondGeopoint,
            "third_point": thirdGeopoint,
            "fourth_point": fourthGeopoint,
            "gates":[]
        }
        fieldEntry.set(docJsonEntry)
        
        #adding fieldID to userColection


        print("field_after",fieldEntry.get().id)
        return jsonify({"success": True})
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
        
        lat,lng = tuple([float (x) for x in request.get_json()["gateLocation"].split("|")])
        gateLocation = GeoPoint(lat,lng)
        #fetchID for gate and height and persisting into gate collection
        gateID = randrange(50)

        gateHeight = randrange(10)
        gateJson = {
            "location":gateLocation,
            "gate_height": 75,
            "node_id":0
        }
        ivCollection.document(str(gateID)).set(gateJson)

        
        # #updating fieldsCollection to add new gate
        # fieldID = request.get_json()["field_id"]
        # currentGates = fields.document(fieldID).get().to_dict()["gates"]
        # currentGates.append(gateID)
        # updatedFieldsDocument = {
        #     "gates":currentGates
        # }
        # fields.document(fieldID).update(updatedFieldsDocument)
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