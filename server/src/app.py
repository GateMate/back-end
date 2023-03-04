# Required imports
import os
import numpy as np
import json
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore, initialize_app
from google.cloud.firestore import GeoPoint
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




@app.route("/",methods = ['GET'])
def start():
     return jsonify({"success": True}), 200


@app.route("/signup", methods =['GET','POST'])
def signUp():
    try:
        newUserId = request.get_json()['userID']
        jsonEntry = {
            'first_name': 'Jose',
            'last_name':'Martinez'
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

        docJsonEntry = {
            "user_id": db.document(currentUserReference).id,
            "field_name":'test_field',
            "first_point" : firstGeopoint,
            "second_point": secondGeopoint,
            "third_point": thirdGeopoint,
            "fourth_point": fourthGeopoint
        }
        fields.document().set(docJsonEntry)
        return jsonify({"success": True})
    except Exception as e:
        return f"An Error Occurred: {e}"

#sample request body
# {
#     "name": "my gate",
#     "location": "50|50"
# }
@app.route("/addGate", methods =['GET','POST'])
def addGates():
    try:
        gateName = request.get_json()["name"]
        lat,lng = tuple([float (x) for x in request.get_json()["location"].split("|")])
        geoPoint = GeoPoint(lat,lng)

        jsonEntry = {
            "user_id": db.document(currentUserReference).id,
            "name": gateName,
            "location": geoPoint
        }
        gatesCollection.document().set(jsonEntry)
        return jsonify({"success": True})
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