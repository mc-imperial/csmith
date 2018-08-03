import os
from random import Random
from hypothesis.internal.conjecture.data import ConjectureData
import sys
from gen_prog import gen
import hashlib
import subprocess

EXAMPLES = os.path.join(os.path.dirname(__file__), "examples")

LIMIT = 100


def results_for_o1_and_o2_differ(sourcename):
    try:
        print("Compiling")
        proc = subprocess.Popen(["gcc", "-O1", "-o", "opt1", "-I", "runtime", sourcename], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, err = proc.communicate()
        if proc.returncode != 0:
            print(err)
            return False
        proc = subprocess.Popen(["gcc", "-O2", "-o", "opt2", "-I", "runtime", sourcename], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, err = proc.communicate()
        if proc.returncode != 0:
            print(err)
            return False
        print("Running 1")
        proc = subprocess.Popen(["./opt1"], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout1, stderr1 = proc.communicate(timeout=0.5)
        if proc.returncode != 0:
            return False
        print("Running 2")
        proc = subprocess.Popen(["./opt2"], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout2, stderr2 = proc.communicate(timeout=0.5)
        if proc.returncode != 0:
            return False
        print("Ran")
        return stdout1 != stdout2
    except subprocess.SubprocessError:
        return False


if __name__ == '__main__':

    try:
        os.makedirs(EXAMPLES)
    except FileExistsError:
        pass

    rnd = Random()

    found = 0
    i = 0
    while found < LIMIT:
        i += 1
        print("Iter", i)
        data = ConjectureData(
            max_length=2**29,
            draw_bytes=lambda self, n: rnd.getrandbits(8 * n).to_bytes(
                n, byteorder='big'
            )
        )

        sourcename = "example.c"

        gen(data, sourcename)

        print("Generated")

        if results_for_o1_and_o2_differ(sourcename):
            found += 1
            print("Found", found)
            result = bytes(data.buffer)
            name = hashlib.sha1(result).hexdigest()[:16]
            with open(os.path.join(EXAMPLES, name), 'wb') as outfile:
                outfile.write(result)
