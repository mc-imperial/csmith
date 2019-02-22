import os
import subprocess
import tempfile
import sys
import shutil

command_writer = result_reader = None


pipeout = None


def write_result(str):
    pipeout = open(result_reader, "w")
    pipeout.write(str + "\0")
    pipeout.flush()
    pipeout.close()


def read_command():
    pipein = open(command_writer, "r")
    line = pipein.readline()[:-1]
    pipein.close()
    return line

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
