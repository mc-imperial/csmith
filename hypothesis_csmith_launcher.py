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

from gen_prog import gen
            
@given(RawDataStrategy())
@settings(verbosity=Verbosity.debug,suppress_health_check=HealthCheck.all(),buffer_size=128000,use_coverage=False)
def test_program_generation(warning, data):

    gen(data, "generatedprog.c")

    try:
        proc = subprocess.Popen(["gcc", "-Wall", "-pedantic", "-I", "runtime", "generatedprog.c"], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()

        if not warning in stderr:
            reject()
           
        proc = subprocess.Popen(["./a.out"], encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate(timeout=3)
    except subprocess.SubprocessError:
        reject()

    prog = "".join(open("generatedprog.c", "r").readlines())
    note(prog)
    note(stdout)
    assert False
        
if __name__ == '__main__':
    test_program_generation("-Wtautological-compare")
