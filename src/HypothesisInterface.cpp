#include "HypothesisInterface.h"

#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <stdlib.h>
#include <assert.h>

#define BUF_SIZE 200

static const char * fifo_commands = getenv("HYPOTHESISFIFOCOMMANDS");
static const char * fifo_results = getenv("HYPOTHESISFIFORESULTS");
static char incoming[BUF_SIZE];
static char outgoing[BUF_SIZE];

static void writeCommand(const char * command) {
  int fd = open(fifo_commands, O_WRONLY);
  strcpy(outgoing, command);
  write(fd, outgoing, strlen(outgoing) + 1);
  close(fd);
}

static void readResult() {
  int fd = open(fifo_results, O_RDONLY);
  read(fd, incoming, sizeof(incoming));
  close(fd);
}

static void getAck() {
  readResult();
  assert(strcmp(incoming, "ACK") == 0);
}

unsigned long hypothesisGetRand() {
  writeCommand("RAND");
  readResult();
  return atol(incoming);
}

void hypothesisInitConnection() {
  mkfifo(fifo_results, 0666);
  mkfifo(fifo_commands, 0666);
}

void hypothesisTerminateConnection() {
  writeCommand("TERMINATE");
  getAck();
}

void hypothesisStartExample(const char *label) {
  int fd = open(fifo_commands, O_WRONLY);
  sprintf(outgoing, "START %s", label);
  assert(strlen(outgoing) > 0);
  write(fd, outgoing, strlen(outgoing) + 1);
  close(fd);
  getAck();
}

void hypothesisEndExample() {
  writeCommand("END");
  getAck();
}
