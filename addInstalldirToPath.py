import os
import sys

path = os.path.realpath(__file__)
path = path[:path.rindex(os.path.sep)]
print(path)
sys.path.insert(0, path)
