from hypothesis.searchstrategy import SearchStrategy
from hypothesis import given, note, settings, Verbosity, HealthCheck
from hypothesis.internal.conjecture.utils import integer_range
from hypothesis import reject

class RawDataStrategy(SearchStrategy):
    def do_draw(self, data):
        return data

import os
import random
import subprocess
import sys

pipe_name = '/tmp/fifo'

def write(str):
    pipeout = open(pipe_name, "w")
    pipeout.write(str + "\0")
    pipeout.close()

def read():
    pipein = open(pipe_name, "r")
    line = pipein.readline()[:-1]
    pipein.close()
    return line

def ack():
    write("ACK")

@given(RawDataStrategy())
@settings(verbosity=Verbosity.debug,suppress_health_check=HealthCheck.all(),buffer_size=32000,use_coverage=False)
def test_program_generation(data):

    try:
        if not os.path.exists(pipe_name):
            os.mkfifo(pipe_name)

        proc = subprocess.Popen(["./src/csmith", "-o", "generatedprog.c"])

        while True:
            line = read()
            if line == "TERMINATE":
                ack()
                break
            elif line == "RAND":
                value = str(data.draw_bits(31))
                note(value)
                write(value)
            elif line == "START":
                data.start_example(1)
                ack()
            elif line == "STOP":
                data.stop_example()
                ack()
            else:
                raise Exception("Unknown command " + line)

        proc.wait()

        try:
            proc = subprocess.Popen(["gcc", "-I", "runtime", "generatedprog.c"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            proc = subprocess.Popen(["./a.out"], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate(timeout=3)
        except subprocess.SubprocessError:
            reject()

        prog = "\n".join(open("generatedprog.c", "r").readlines())
        note(prog)
        note(stdout)
        
        assert not stdout.startswith("checksum = A")
        
    finally:
        try:
            proc.kill()
        except OSError:
            pass

if __name__ == '__main__':
    test_program_generation()
