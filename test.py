import requests
from os import environ as env

TEST_FIELD_ID = env.get('TEST_FIELD_ID')
ENDPOINT = "https://todo-proukhgi3a-uc.a.run.app/tile-field"

# Number of tiles in each direction, currently
# by default this is an 8x8, a smaller value 
# gives a lower resolution in the height map
FIELD_DIM_X = int(env.get('FIELD_DIM_X')) if env.get('FIELD_DIM_X') != None else 8
FIELD_DIM_Y = int(env.get('FIELD_DIM_Y')) if env.get('FIELD_DIM_Y') != None else 8

BODY = {}
BODY["fieldID"] = TEST_FIELD_ID

print("COMMENCING TEST... (this may take a bit)")

response = requests.post(
    url=ENDPOINT,
    json=BODY
)

print("GOT RESPONSE!")

tiles_dict = {}

if (response.status_code == 200):
    data = {}
    data = response.json()

    tiles_dict = data

    print("TEST OUTPUT BELOW\n")

    # Default config of the server function is a max 
    # of 4 normalized tile height levels,
    # so we only need to support 4 distinct heights
    # in the test output

    for i in range(FIELD_DIM_Y):
        for j in range(FIELD_DIM_X):
            match tiles_dict[str(i*FIELD_DIM_X +j)]["height_val"]:
                case 0:
                    print("\033[1;32mO ", end="")
                case 1:
                    print("\033[1;33mO ", end="")
                case 2:
                    print("\033[1;34mO ", end="")
                case _:
                    print("\033[1;35mO ", end="")

        print("")

    print("\033[0m\nEND OF TEST")
else:
    print("ERROR: RESPONSE CODE = ", str(response.status_code))