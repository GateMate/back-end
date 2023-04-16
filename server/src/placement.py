import numpy as np
import requests

TILES_PER_FIELD_Y = 8
TILES_PER_FIELD_X = 8

MAX_HEIGHT_LEVELS = 4

ELEVATION_ENDPOINT = "http://34.174.221.76"

# Grabbed this from Geeks4Geeks because I don't need to write this myself
def closest(lst, K):
    return lst[min(range(len(lst)), key = lambda i: abs(lst[i]-K))]

def tileField(current_field: dict) -> dict:

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

	return tiles_dict