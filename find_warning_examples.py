import os
from random import Random
from hypothesis.internal.conjecture.data import ConjectureData
import sys
from gen_prog import gen
import hashlib
import subprocess

EXAMPLES = os.path.join(os.path.dirname(__file__), "examples")

LIMIT = 5


def compiler_emits_warning_and_program_terminates(warning, sourcename):
    try:
        proc = subprocess.Popen(["gcc", "-Wall", "-pedantic", "-I", "runtime", sourcename], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if not warning in stderr:
            return False
        proc = subprocess.Popen(["./a.out"], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.communicate(timeout=3)
    except subprocess.SubprocessError:
        return False
    return True


if __name__ == '__main__':

    warning = sys.argv[1]
    
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

        if compiler_emits_warning_and_program_terminates(warning, sourcename):
            found += 1
            print("Found", found)
            result = bytes(data.buffer)
            name = hashlib.sha1(result).hexdigest()[:16]
            with open(os.path.join(EXAMPLES, name), 'wb') as outfile:
                outfile.write(result)
