from firebase_admin import credentials, firestore, initialize_app, auth, _auth_utils, App
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
    
    def deleteField(self, fieldID) -> bool:
        try:
            self.fields.document(fieldID).delete()
            return True
        except Exception:
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
        
    def fetchGates(self) -> tuple:
        try:
            gates_json = {}

            gates = self.gates.stream()
            for gate in gates:
                gates_json[gate.id] = {
                    "lat": gate.to_dict()["lat"],
                    "long": gate.to_dict()["long"],
                    "height": gate.to_dict()["height"],
                    "nodeID": gate.to_dict()["nodeID"]
                }
            
            return True, gates_json
        except Exception:
            return False, {}
        
    def getField(self, fieldID) -> tuple:
        try:
            return True, self.fields.document(fieldID).get().to_dict()
        except Exception:
            return False, {}
        
    def fetchFields(self) -> tuple:
        try:
            fields_list = self.fields.stream()
            id_list = [field.id for field in fields_list]

            fields_json = json.dumps(id_list)
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
        
    def getFieldTiles(self, fieldID) -> tuple:
        try:
            return (True, placement.tileField(
                self.getField(fieldID=fieldID)[1]
            ))
        except Exception:
            return False, {}
    
    def initUser(self, userID) -> bool:
        initial_user = {
            "fields":[],
            "todos":[]
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

    def createToDo(self, title, toDoID=-1):
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
        
    def deleteToDo(self, toDoID) -> bool:
        try:
            self.todos.document(toDoID).delete()

            return True
        except Exception:
            return False









        
        