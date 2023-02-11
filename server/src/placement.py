import numpy as np
import random
#placeholder function for generating gate placements
def generateGatePlacement(latitude, longitude, map: np.array):
	print("here1")
	gatePlacements = np.empty([4,3])
	# gatePlacements.shape = (4, 3) #3 is what matters. 0=lat. 1=long. 2=extra info like maybe gate number
	print("here2")
	for x in range(0, 4):
		latoff = random.uniform(-0.01, 0.01)
		longoff = random.uniform(-0.01, 0.01)
		gatePlacements[x, 0] = latitude+latoff
		gatePlacements[x, 1] = longitude+longoff
		gatePlacements[x, 2] = x
	return gatePlacements