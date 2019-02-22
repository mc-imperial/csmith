import os
import subprocess
import tempfile
import sys
import shutil

command_writer = result_reader = None


pipeout = pipein = None


def write_result(str):
    global pipeout
    if pipeout is None:
        pipeout = open(result_reader, "w")
    pipeout.write(str + "\n")
    pipeout.flush()


def read_command():
    global pipein
    if pipein is None:
        pipein = open(command_writer, "rb")
    while True:
        c = pipein.read(1)
        if not c:
            continue
        n = c[0]
        return pipein.read(n).decode('ascii')

def ack():
    write_result("ACK")

def gen(data, output_name):
    global command_writer, result_reader

    env = dict(os.environ)
    pipe_dir = tempfile.mkdtemp()
    command_writer = os.path.join(pipe_dir, "hypothesisfifo.commands")
    result_reader = os.path.join(pipe_dir, "hypothesisfifo.results")
    env["HYPOTHESISFIFOCOMMANDS"] = command_writer
    env["HYPOTHESISFIFORESULTS"] = result_reader

    os.mkfifo(command_writer)
    os.mkfifo(result_reader)
    
    proc = subprocess.Popen(["./src/csmith", "-o", output_name], env=env, stdout=sys.stdout, stderr=sys.stderr)
    try:
        while True:
            line = read_command()
            if line == "TERMINATE":
                ack()
                break
            elif line == "RAND":
                value = str(data.draw_bits(31))
                write_result(value)
            elif line.startswith("START "):
                _, label = line.split()
                data.start_example(label.strip())
                ack()
            elif line == "END":
                data.stop_example()
                ack()
            # Terminated improperly
            elif not line:
                break
            else:
                raise Exception("Unknown command %r" % (line,))

        proc.wait()

    finally:
        try:
            proc.kill()
        except OSError:
            pass
        shutil.rmtree(pipe_dir)
