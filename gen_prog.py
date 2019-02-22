import os
import subprocess
import tempfile
import sys
import shutil

pipe_name = None

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

def gen(data, output_name):
    global pipe_name

    env = dict(os.environ)
    pipe_dir = tempfile.mkdtemp()
    pipe_name = os.path.join(pipe_dir, "hypothesisfifo")
    env["HYPOTHESISFIFO"] = pipe_name

    os.mkfifo(pipe_name)
    
    proc = subprocess.Popen(["./src/csmith", "-o", output_name], env=env, stdout=sys.stdout, stderr=sys.stderr)
    try:
        while True:
            line = read()
            if line == "TERMINATE":
                ack()
                break
            elif line == "RAND":
                value = str(data.draw_bits(31))
                write(value)
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
