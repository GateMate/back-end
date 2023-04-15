# Required imports
import os
import numpy as np
import json
from flask import Flask, request, jsonify
from firebase_admin import credentials, auth, _auth_utils
from weather_api import requestWeather
import FB_interface

# class NumpyEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, np.ndarray):
#             return obj.tolist()
#         return json.JSONEncoder.default(self, obj)

# Initialize Flask app
app = Flask(__name__)

# Initialize database instance
fbInter= FB_interface.FBInterface(credentials.Certificate('key.json'))

#main link: https://todo-proukhgi3a-uc.a.run.app

def check_auth(request: Flask.request_class):
    token = ""
    if request.method == "GET":
        token = request.headers.get('Authorization')
    else:
        try: 
            token = request.get_json()['auth_token']
        except KeyError:
            token = request.headers.get('Authorization')
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']

        return True, uid
    except _auth_utils.InvalidIdTokenError:
        return False, ""

def updateFieldDocument(fieldID,gateID):
    try:
        field_json = fbInter.updateField(fieldID, gateID)
        if (field_json[0]):
            return field_json[1], 200
        else:
            return ("Internal Server Error", 500)
    except Exception as e:
        return f"An Error Occurred: {e}"

#the addField and addGate routes will not work until the user signs in(sign in route)
@app.route("/",methods = ['GET'])
def start():
     return jsonify({"success": True})

@app.route("/weather_forecast/<lat>/<long>", methods = ['GET'])
def getWeather(lat = 0.0, long=0.0):
    if (check_auth(request)[0]):
        try:
            forecast_data = requestWeather(lat, long)#(36.082157, -94.171852)
            forecast_hourly = forecast_data['hourly']
            #print(forecast_hourly.keys())
            #print(forecast_data['hourly']) 
            return (
                jsonify(
                    {"precipitation_hourly": forecast_hourly['precipitation'], 
                    "timedate_hourly": forecast_hourly['time']}
                    ), 
                200
            )
        except:
            return jsonify(({"error":"error occured with weather api"})), 500
    else:
        return ("FORBIDDEN", 403)


# sampleRequestBody - key:gateID value:newNodeId
# {
#   "XpRSItWlLGa1b4NuDvJn" : "10"a
# }
@app.route("/updateNodeId", methods = ["GET","POST"])
def updateNodeId():
    if (check_auth(request)[0]):
        try:
            gate_id = request.get_json()['gateID']
            node_id = request.get_json()['nodeID']

            if (fbInter.updateNodeID(gate_id, node_id)):       
                return ("OK", 200)
            else: 
                return ("Internal Server Error", 500)
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)

@app.route("/deleteField",methods = ['GET','POST'])
def deleteField():
    if (check_auth(request)[0]):
        try:
            fieldID = request.get_json()['fieldID']
            if (fbInter.deleteField(fieldID)):
                return ("OK", 200)
            else:
                return ("Internal Server Error", 500)
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
    if (check_auth(request)[0]):
        if (fbInter.initUser(check_auth(request)[1])):
            return jsonify({"success": True}), 200
        else:
            return ("Internal Server Error", 500)
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
    current_auth = check_auth(request)
    if (current_auth[0]):
        try:
            firstGeopoint = request.get_json()['nw']
            secondGeopoint = request.get_json()['ne']
            thirdGeopoint = request.get_json()['sw']
            fourthGeopoint = request.get_json()['se']

            new_field = fbInter.createField(
                firstGeopoint,
                secondGeopoint,
                thirdGeopoint,
                fourthGeopoint
            )

            if (new_field[0]):
                fieldID = {
                    "fieldID": new_field[1]
                }

                fbInter.updateUserField(new_field[1], current_auth[1])

                return (jsonify(fieldID), 200)
            else:
                return "Internal Server Error", 500
            
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
    if (check_auth(request)[0]):
        try:
            gateHeight = request.get_json()['height']
            gateID = request.get_json()['gateID']

            if (fbInter.setGateHeight(
                gateID=gateID, 
                newHeight=gateHeight)):

                return ("OK", 200)
            else:
                return ("Internal Server Error", 500)
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
    if (check_auth(request)[0]):
        try:
            lat,long = tuple(request.get_json()["gateLocation"].split("|"))
            fieldID = request.get_json()["fieldID"]

            new_gate = fbInter.createGate(
                lat=lat,
                long=long, 
                fieldID=fieldID
            )

            if (new_gate[0]):
                fbInter.updateField(fieldID, new_gate[1])
            
                return ("OK", 200)
            else:
                return ("Internal Server Error", 500)
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:   
        return ("FORBIDDEN", 403)

@app.route("/getGates",methods = ['GET','POST'])
def fetchGates():
    current_auth = check_auth(request)
    if (current_auth[0]):
        try:
            gates = None
            if (request.args.get('fieldID') != None):
                gates = fbInter.fetchGates(current_auth[1], request.args.get('fieldID'))
            else:
                gates = fbInter.fetchGates(current_auth[1])
            if (gates[0]):
                return jsonify(gates[1]), 200
            else:
                return ("Internal Server Error", 500)
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)
    
@app.route('/getField', methods=['GET','POST'])
def getField():
    current_auth = check_auth(request)
    if (current_auth[0]):
        fieldID = ""
        if (request.method == "GET"):
            fieldID = request.args.get('fieldID')
        else:
            fieldID = request.get_json()['fieldID']
        try:
            field_dict = fbInter.getField(fieldID=fieldID, userID=current_auth[1])
            if (field_dict[0]):        
                return (jsonify(field_dict[1]), 200)
            else:
                if (field_dict[1]['response'] == 403):
                    return ("FORBIDDEN", 403)
                else:
                    return ("Internal Server Error", 500)
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403) 


@app.route('/getFields', methods=['GET','POST'])
def getFields(): 
    current_auth = check_auth(request)
    if (current_auth[0]):
        fieldResponse = []
        try:
            fields = fbInter.fetchFields(current_auth[1])
            if (fields[0]):
                return fields[1], 200
            else:
                return (jsonify({"success": False}), 500)
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)\


#sample request body
# {
#     "gateID":"5bVRcE4HoyhO9JnAXG1w",
#     "location":"50|40"
# }
@app.route('/adjustGateLocation', methods=['GET','POST'])
def adjustGateLocation():
    if (check_auth(request)[0]):
        try:
            lat = request.get_json()["location"].split("|")[0]
            long = request.get_json()["location"].split("|")[1]
            gateID = request.get_json()['gateID']

            if (fbInter.setGateLocation(
                gateID=gateID,
                lat=lat,
                long=long
            )):
                return ("OK", 200)
            else:
                return ("Internal Server Error", 500)
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
    if (check_auth(request)[0]):
        try:
            field_id = request.get_json()["fieldID"]
            tiled_field = fbInter.getFieldTiles(fieldID=field_id)

            if (tiled_field[0]):
                return jsonify(tiled_field[1]), 200      
            else:
                return ("Internal Server Error", 500)
        except Exception as e:
            return f"An Error Occurred: {e}"
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
    if (check_auth(request)[0]):  
        try:
            to_do_title = request.get_json()['title']
            try:
                to_do_id = request.get_json()['id']
                new_to_do = fbInter.createToDo(
                    title=to_do_title, toDoID=to_do_id
                )
            except KeyError:
                new_to_do = fbInter.createToDo(
                    title=to_do_title
                )
            if (new_to_do[0]):
                return ("OK", 200)
            else:
                return ("Internal Server Error", 500)
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
    if (check_auth(request)[0]):  
        try:
            # Check if ID was passed to URL query
            todo_id = request.args.get('id')
            to_do = None
            if todo_id:
                to_do = fbInter.getToDo(toDoID=todo_id)
            else:
                to_do = fbInter.getToDo()
            
            if (to_do[0]):
                return jsonify(to_do), 200
            else:
                return ("Internal Server Error", 500)
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
    if (check_auth(request)[0]):

        try:
            id = request.get_json()['id']
            title = request.get_json()['title']
            
            if (fbInter.updateToDo(id, title)):
                return ("OK", 200)
            else:
                return ("Internal Server Error", 500)
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)

@app.route('/delete', methods=['GET', 'DELETE'])
def delete():
    """
        delete() : Delete a document from Firestore collection.
    """
    if (check_auth(request)[0]):
        try:
            # Check for ID in URL query
            todo_id = request.args.get('id')
            if (fbInter.deleteToDo(todo_id)):
                return ("OK", 200)
            else:
                return ("Internal Server Error", 500)
        except Exception as e:
            return f"An Error Occurred: {e}"
    else:
        return ("FORBIDDEN", 403)

port = int(os.environ.get('PORT', 8080))
if __name__ == '__main__':
    app.run(threaded=True, host='0.0.0.0', port=port)