import numpy as np

fixations = [[1,2,9,8,7], [3,4,2,3,4], [5,6,5,6,7]]
fixations = np.array(fixations)
x = fixations[0, 0:3]
y = fixations[0:2, 1]

print(x)