import os
import subprocess
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

def gen(data, output_name):

    if not os.path.exists(pipe_name):
        os.mkfifo(pipe_name)
    
    try:

        proc = subprocess.Popen(["./src/csmith", "-o", output_name])

        while True:
            line = read()
            if line == "TERMINATE":
                ack()
                break
            elif line == "RAND":
                value = str(data.draw_bits(31))
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

    finally:
        try:
            proc.kill()
        except OSError:
            pass
