from hypothesis.searchstrategy import SearchStrategy
from hypothesis import given, note, settings, Verbosity, HealthCheck, unlimited, assume
from hypothesis.internal.conjecture.utils import integer_range
from hypothesis import reject
import hypothesis.strategies as st
from hypothesis.internal.conjecture.data import ConjectureData, StopTest, Status, Overrun
import hypothesis.internal.conjecture.engine as eng
from random import Random
import os
import traceback
import click
from collections import defaultdict
from hypothesis.core import encode_failure
import time
import tracemalloc

import os
import random
import subprocess
import sys
from glob import glob
import json

from gen_prog import gen
import hashlib
import tempfile
import shutil

BUFFER_SIZE = 10**6

GCCS = glob("/opt/compiler-explorer/gcc-*/bin/gcc")

TIMEOUT = 5

ROOT = os.path.abspath(os.path.dirname(__file__))
RUNTIME = os.path.join(ROOT, "runtime")

def rmf(f):
    try:
        os.unlink(f)
    except FileNotFoundError:
        pass


def run_gcc(gcc, opt, prog):
    with tempfile.TemporaryDirectory() as d:
        env = dict(os.environ)
        env["LIBRARY_PATH"] = "/usr/lib/x86_64-linux-gnu"

        out = os.path.join(d, 'a.out')
        try:
            x = subprocess.check_output(
                [gcc, opt, "-I", RUNTIME, prog, '-o', out], cwd=d,
                stderr=subprocess.DEVNULL,
                timeout=TIMEOUT, env=env
            ).strip()
            return subprocess.check_output([out, "1"], timeout=TIMEOUT)
        finally:
            rmf(out)


def preprocess(text):
    gcc = "/opt/compiler-explorer/gcc-8.2.0/bin/gcc"

    with tempfile.TemporaryDirectory() as d:
        prog = os.path.join(d, "prog.c")
        with open(prog, 'w') as o:
            o.write(text)

        env = dict(os.environ)
        env["LIBRARY_PATH"] = "/usr/lib/x86_64-linux-gnu"

        return subprocess.check_output(
            [gcc, "-I", RUNTIME, prog, '-E', '-P'], cwd=d,
            stderr=subprocess.DEVNULL,
            env=env, encoding='utf-8'
        ).strip()
        

def is_valid(text):
    gcc = "/opt/compiler-explorer/gcc-8.2.0/bin/gcc"

    with tempfile.TemporaryDirectory() as d:
        prog = os.path.join(d, "prog.c")
        with open(prog, 'w') as o:
            o.write(text)

        env = dict(os.environ)
        env["LIBRARY_PATH"] = "/usr/lib/x86_64-linux-gnu"

        return subprocess.call(
            [gcc, "-I", RUNTIME, "-c", prog], cwd=d,
            stderr=subprocess.DEVNULL,
            env=env, encoding='utf-8'
        ) == 0

def interesting_reason(prog, printing=True):
    outputs = set()

    for gcc in GCCS:
        for opt in ['-O0', '-O1', '-O2', '-Os']:
            d = tempfile.mkdtemp()

            out = os.path.join(d, 'a.out')
            runtime = os.path.abspath(os.path.join(os.path.dirname(__file__), "runtime"))

            try:
                env = dict(os.environ)
                env["LIBRARY_PATH"] = "/usr/lib/x86_64-linux-gnu"

                x = subprocess.check_output([gcc, opt, "-I", runtime, prog, '-o', out], timeout=TIMEOUT, env=env, cwd=d, stderr=subprocess.DEVNULL).strip()
                outputs.add(subprocess.check_output([out], timeout=TIMEOUT))
                if len(outputs) > 1:
                    if printing:
                        print(f"Differing output at {gcc} {opt}")
                    return ("differs", gcc, opt)
            except subprocess.TimeoutExpired:
                if printing:
                    traceback.print_exc()
                return None
            except subprocess.SubprocessError as e:
                if printing:
                    print(gcc)
                    print(e.stderr)
                    traceback.print_exc()
                return ("error", gcc, opt)
            finally:
                shutil.rmtree(d)
    return None

def is_interesting(prog):
    return interesting_reason(prog) is not None


@click.group()
def main():
    pass


examples = os.path.abspath('hypothesis-examples')
raw = os.path.join(examples, 'raw')
programs = os.path.join(examples, 'programs')
shrinks = os.path.join(examples, 'shrinks')
for f in [raw, programs, shrinks]:
    try:
        os.makedirs(f)
    except FileExistsError:
        pass


@main.command()
def cleanup():
    files = glob('hypothesis-examples/raw/*')
    Random().shuffle(files)

    for f in files:
        try:
            with open(f, 'rb') as i:
                data = ConjectureData.for_buffer(i.read())
        except FileNotFoundError:
            continue

        with tempfile.TemporaryDirectory() as d:
            prog = os.path.join(d, 'test.c')

            try:
                gen(data, prog)
            except StopTest:
                continue

            name = os.path.basename(f)

            if not is_interesting(prog):
                print(f"Removing {name}")
                rmf(os.path.join(raw, name))
                rmf(os.path.join(programs, name + '.c'))


@main.command()
def fuzz():            

    def try_data(data):
        with tempfile.TemporaryDirectory() as d:
            prog = os.path.join(d, 'test.c')

            try:
                gen(data, prog)
            except StopTest:
                rmf(prog)
                return

            name = hashlib.sha1(data.buffer).hexdigest()[:8]

            print(name)

            if is_interesting(prog):
                with open(os.path.join(raw, name), 'wb') as o:
                    o.write(data.buffer)
                shutil.move(prog, os.path.join(programs, name + '.c'))
            else:
                rmf(os.path.join(raw, name))
                rmf(os.path.join(programs, name + '.c'))

    random = Random()

    while True:
        try_data(ConjectureData(
            max_length=BUFFER_SIZE,
            draw_bytes=lambda self, n: random.getrandbits(n * 8).to_bytes(n, 'big')
        ))


def mktemp(*args, **kwargs):
    pid, name = tempfile.mkstemp(*args, **kwargs)
    os.close(pid)
    return name


def bytes_to_text(b):
    return data_to_text(ConjectureData.for_buffer(b))


def data_to_text(data):
    prog = mktemp(suffix='.c')
    try:
        gen(data, prog)
        with open(prog) as i:
            return i.read()
    finally:
        os.unlink(prog)


@main.command()
@click.argument('filename')
def show(filename):
    with open(filename, 'rb') as i:
        initial_data = ConjectureData.for_buffer(i.read())
    prog = mktemp(suffix='.c')
    try:
        gen(initial_data, prog)
        with open(prog) as i:
            print(i.read())
    finally:
        os.unlink(prog)


@main.command()
@click.option('--seed', default=0)
@click.option('--count', default=100)
@click.option('--max-size', default=-1)
def sample(seed, count, max_size):
    random = Random(seed)

    names = os.listdir(raw)
    names.sort()
    random.shuffle(names)

    printed = 0

    for n in names:
        with open(os.path.join(raw, n), 'rb') as i:
            buffer = i.read()
        if max_size > 0 and len(buffer) > max_size:
            continue

        initial_data = ConjectureData.for_buffer(buffer)
        prog = os.path.join(programs, n + '.c')
        with open(prog, 'r') as i:
            already_good = is_valid(prog)

        if not already_good:
            try:
                gen(initial_data, prog)
            except StopTest:
                continue

        if not interesting_reason(prog, printing=False):
            continue

        print(n)
        printed += 1
        if printed >= count:
            break


@main.command()
def dump_sizes():
    names = list(filter(None, [l.strip() for l in sys.stdin]))

    def raw_programs_in_order():
        grouped = defaultdict(list)
       
        files = [os.path.join(raw, n) for n in names]
        for f in files:
            grouped[os.stat(f).st_size].append(f)

        for n, group in sorted(grouped.items()):
            values = [] 
            for f in group:
                with open(f, 'rb') as i:
                    values.append((i.read(), os.path.basename(f)))
            assert len(set(map(len, values))) == 1
            values.sort()
            yield from values

    for index, (buffer, n) in enumerate(raw_programs_in_order()):
        generated = os.path.join(programs, n + ".c")

        with open(generated) as i:
            text = i.read()

        print(json.dumps({"input": len(buffer), "output": len(text)}))


@main.command()
@click.argument('filename')
@click.option('--sizes', default=None)
def shrink(filename, sizes):
    with open(filename, 'rb') as i:
        initial_data = ConjectureData.for_buffer(i.read())

    printing_to_stdout = False

    def data_info(data):
        name = hashlib.sha1(data.buffer).hexdigest()[:8]
        input_length = len(data.buffer)
        output_length =  data.extra_information.generated_length

        return {
            "name": name, "input_length": input_length, "output_length": output_length,
            "interesting": data.status == Status.INTERESTING
        }

    if sizes is not None:
        if sizes == "-":
            writer = sys.stdout
            printing_to_stdout = True
        else:
            writer = open(sizes, 'w')

        def log_data(data):
            if data.status >= Status.VALID and hasattr(data.extra_information, 'generated_length'):
                writer.write(json.dumps(data_info(data)) + "\n")
                writer.flush()
    else:
        writer = None
        def log_data(data):
            pass

    initial = mktemp(suffix='.c') 
    gen(initial_data, initial)
    errtype, gcc, opt = interesting_reason(initial, printing=not printing_to_stdout)

    if errtype == 'error':
        def test_function(data):
            with tempfile.TemporaryDirectory() as d:
                prog = os.path.join(d, 'test.c')

                try:
                    gen(data, prog)
                    data.extra_information.generated_length = os.stat(prog).st_size
                    run_gcc(gcc, opt, prog)
                except subprocess.TimeoutExpired:
                    return
                except subprocess.SubprocessError:
                    name = hashlib.sha1(data.buffer).hexdigest()[:8]
                    data.unique_name = name
                    data.mark_interesting()
                finally:
                    log_data(data)
    else:
        assert errtype == "differs"
        
        def test_function(data):
            with tempfile.TemporaryDirectory() as d:
                prog = os.path.join(d, 'test.c')

                try:
                    gen(data, prog)
                    data.generated_length = os.stat(prog).st_size
                    if run_gcc(gcc, opt, prog) != run_gcc(
                        '/opt/compiler-explorer/gcc-8.2.0/bin/gcc', '-O0', prog
                    ):
                        name = hashlib.sha1(data.buffer).hexdigest()[:8]
                        data.unique_name = name
                        data.mark_interesting()
                except subprocess.SubprocessError:
                    pass
                finally:
                    log_data(data)

    eng.MAX_SHRINKS = 10 ** 6

    with open(filename, 'rb') as i:
        buffer = i.read()

    # tracemalloc.start()

    runner = eng.ConjectureRunner(test_function, settings=settings(
        database=None,
        max_examples=1000,
        timeout=unlimited, suppress_health_check=HealthCheck.all(),
        deadline=None,
        verbosity=Verbosity.quiet if printing_to_stdout else Verbosity.debug,
        buffer_size=BUFFER_SIZE
    ), random=Random(int.from_bytes(hashlib.sha1(buffer).digest(), 'big')))


    class FakeTree(object):
        def add(self, data):
            pass

        def rewrite(self, buffer):
            return (buffer, None)

        def generate_novel_prefix(self, random):
            return b''

        is_exhausted = False


    def uncached_test_function(buffer):
        data = ConjectureData.for_buffer(buffer)
        runner.test_function(data)

#       snapshot = tracemalloc.take_snapshot()
#       top_stats = snapshot.statistics('lineno')

        print("[ Top 10 ]")
        for stat in top_stats[:10]:
            print(stat)

        return data.as_result()

#   runner.tree = FakeTree()
#   runner.cached_test_function = uncached_test_function
#   runner.target_selector.add = lambda x: None

    runner.test_function(ConjectureData.for_buffer(buffer))

    assert runner.interesting_examples

    runner.debug_data = lambda data: runner.debug(
        f"DATA({getattr(data, 'unique_name', None)}): {len(data.buffer)} bytes, {data.status.name}, {data.interesting_origin}"
    )

    v, = runner.interesting_examples.values()

    shrinker = runner.new_shrinker(
        v, lambda d: d.status == Status.INTERESTING and d.interesting_origin == v.interesting_origin
    )

    initial_calls = runner.call_count
    initial_valid = runner.valid_examples
    start = time.monotonic()
    shrinker.shrink()
    end = time.monotonic()
    final = data_info(shrinker.shrink_target)
    final["bytes"] = encode_failure(shrinker.shrink_target.buffer).decode('ascii')

    if writer is not None:
        writer.write(json.dumps({
            "runtime": end - start,
            "calls": runner.call_count - initial_calls,
            "valid": runner.valid_examples - initial_valid,
            "final": final,
        }) + "\n")

    result = runner.interesting_examples[v.interesting_origin]
    runner.debug_data(result)

    gen(ConjectureData.for_buffer(result.buffer), 'shrunk.c')
    if writer is not None:
        writer.close()


if __name__ == '__main__':
    main()
