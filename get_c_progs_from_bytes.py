import os
from hypothesis.internal.conjecture.data import ConjectureData
import sys
from gen_prog import gen

def generate_from_bytes(filename):
    if filename.endswith(".c"):
        return
    with open(filename, 'rb') as infile:
        data = ConjectureData.for_buffer(infile.read())
    gen(data, filename + ".c")
    
if __name__ == '__main__':

    target = sys.argv[1]

    if os.path.isdir(target):
        for root, dirs, files in os.walk(target):
            for file in files:
                generate_from_bytes(root + os.sep + file)
    elif os.path.isfile(target):
        generate_from_bytes(target)
    
