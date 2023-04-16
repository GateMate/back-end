from firebase_admin import credentials, firestore, initialize_app, App
import google.cloud.firestore as gcfirestore
import json
import placement

#this should be an environment variable eventually
ELEVATION_ENDPOINT = "http://34.174.221.76"

class FBInterface:
    def __init__(self, credentials: credentials.Certificate):
        try:
            self.app: App = initialize_app(credential=credentials)
            self.db : gcfirestore.Client = firestore.client() 

            self.fields = self.db.collection('fields')
            self.gates = self.db.collection('gates')
            self.users = self.db.collection('users')
            self.todos = self.db.collection('todos')
        except ValueError:
            print("UNABLE TO INITIALIZE FIRESTORE DATABASE!")

    def updateField(self, fieldID: str, gateID: str) -> tuple:
        try:
            field = self.fields.document(fieldID)
            field.update({
                u'gates': firestore.ArrayUnion([str(gateID)])
            })
            fields_as_json: dict = self.fields.document(
                fieldID
            ).get().to_dict()

            return True, fields_as_json
        except Exception as e: 
            return False, {}
    
    def getField(self, fieldID) -> tuple:
        print("getting field")
        try:
            print("hi")
            print(self.fields.document(fieldID).get().to_dict())
            return True, self.fields.document(fieldID).get().to_dict()
        except Exception:
            return False, {}
    
    def deleteField(self, fieldID, userID) -> bool:
        try:
            self.fields.document(fieldID).delete()

            user = self.users.document(userID).get().to_dict()
            user_fields = list(user['fields'])
            
            user_fields.remove(fieldID)
            user['fields'] = user_fields

            self.users.document(userID).update(user)
            return True
        except Exception as e:
            print(e)
            return False
    
    def createField(self, nwPoint, nePoint, swPoint, sePoint, name="") -> tuple:
        try:
            field_json = {
                "field_name": name,
                "nw_point": nwPoint,
                "ne_point": nePoint,
                "sw_point": swPoint,
                "se_point": sePoint,
                "gates": []
            }

            field_entry = self.fields.document()
            field_entry.set(field_json)
            field_id = field_entry.id

            return True, field_id
        except Exception as e:
            return False, e
    
    def setGateHeight(self, gateID, newHeight: str) -> bool:
        try:
            updated_gate = {"height": newHeight}
            self.gates.document(gateID).update(
                updated_gate
            )
            
            return True
        except Exception:
            return False
    
    def createGate(self, lat, long, fieldID, height=0, nodeID=-1) -> tuple:
        try:
            new_gate = self.gates.document()

            gate_json = {
                "lat": lat,
                "long": long,
                "nodeID": nodeID,
                "height": height
            }

            new_gate.set(gate_json)
            gate_id = new_gate.id
            
            self.updateField(fieldID=fieldID, gateID=gate_id)

            return True, gate_id
        except Exception:
            return False, ""
        
    def fetchGates(self, userID, fieldID = -1) -> tuple:
        print(fieldID)
        try:
            gates_json = {}
            gates = []

            if (fieldID == -1):
                for field in self.users.document(userID).get().to_dict()['fields']:
                    for gate in self.fields.document(field).get().to_dict()['gates']:
                        gates.append(gate)

                for gate in gates:
                    current_gate = self.gates.document(gate).get().to_dict()

                    gates_json[self.gates.document(gate).id] = {
                        "lat": current_gate["lat"],
                        "long": current_gate["long"],
                        "height": current_gate["height"],
                        "nodeID": current_gate["nodeID"]
                    }
                
                return True, gates_json
            else:
                print(userID)
                current_field = self.getField(fieldID, userID)[1]

                print(current_field)

                for gate in current_field['gates']:
                    current_gate = self.gates.document(gate).get().to_dict()

                    print(current_gate)

                    gates_json[self.gates.document(gate).id] = {
                        "lat": current_gate["lat"],
                        "long": current_gate["long"],
                        "height": current_gate["height"],
                        "nodeID": current_gate["nodeID"]
                    }

                return True, gates_json
        except Exception:
            return False, {}
        
    def getField(self, fieldID, userID) -> tuple:
        try:
            if (fieldID in self.users.document(userID).get().to_dict()['fields']):
                return True, self.fields.document(fieldID).get().to_dict()
            else:
                return False, {"response": 403}
        except Exception:
            return False, {"response": 500}
        
    def fetchFields(self, userID) -> tuple:
        try:
            user_data = self.users.document(userID).get().to_dict()
            fields = user_data['fields']

            print(fields)
            fields_json = json.dumps(fields)
            return True, fields_json
        except Exception:
            return False, {}
    
    def setGateLocation(self, gateID, lat, long) -> bool:
        try:
            updated_gate = {
                "lat": lat,
                "long": long
            }

            self.gates.document(gateID).update(updated_gate)

            return True
        except:
            return False
        
    def getFieldTiles(self, fieldID, userID) -> tuple:
        try:
            field = self.getField(fieldID=fieldID, userID=userID)

            print(field)

            return (True, placement.tileField(
                field[1]
            ))
        except Exception:
            return False, {}
    
    def initUser(self, userID, firstName, lastName) -> bool:
        initial_user = {
            "fields":[],
            "todos":[],
            "firstName": firstName,
            "lastName": lastName
        }
        try:
            self.users.document(str(userID)).set(initial_user)
            return True
        except Exception:
            return False
    
    def activateUser(self, userID):
        active_json = {
            "activeUser": "true"
        }
        try:
            self.users.document(userID).update(active_json)
            return True
        except Exception:
            return False
        
    def deactivateUser(self, userID):
        active_json = {
            "activeUser": "false"
        }
        try:
            self.users.document(userID).update(active_json)
            return True
        except Exception:
            return False
    
    def updateNodeID(self, gateID, newNodeID):
        node_json = {
            "nodeID": newNodeID
        }

        try:
            self.gates.document(gateID).update(node_json)
            return True
        except Exception:
            return False
    
    def updateUserField(self, fieldID, userID):
        user = self.users.document(userID)

        user.update({u'fields': firestore.ArrayUnion([str(fieldID)])})

    def updateUserTodo(self, userID, todoID):
        user = self.users.document(userID)

        user.update({u'todos': firestore.ArrayUnion([str(todoID)])})

    def createToDo(self, title, userID, toDoID=-1):
        new_to_do = None
        if (toDoID == -1):       
            new_to_do = {
                "title": title
            }
        else:
            new_to_do = {
                "title": title,
                "id": toDoID
            }
        try:
            to_add = self.todos.document()
            to_add.set(new_to_do)

            self.updateUserTodo(userID, to_add.id)

            return True, to_add.id
        except Exception:
            return False, ""
    
    def getToDo(self, toDoID = -1) -> tuple:
        try:
            if (toDoID != -1):
                return (
                    True, 
                    self.todos.document(toDoID).get().to_dict()
                )
            else:
                return (
                    True, 
                    [doc.to_dict() for doc in self.todos.stream()]
                )
        except Exception:
            return False, []
        
    def updateToDo(self, toDoID, title) -> bool:
        try:
            new_to_do = {
                "title": title
            }

            self.todos.document(toDoID).update(new_to_do)

            return True
        except Exception:
            return False
        
    def deleteToDo(self, toDoID, userID) -> bool:
        try:
            self.todos.document(toDoID).delete()

            user = self.users.document(userID).get().to_dict()
            user_todos = list(user['todos'])
            
            user_todos.remove(toDoID)
            user['todos'] = user_todos

            self.users.document(userID).update(user)

            return True
        except Exception as e:
            print(e)
            return False









        
        