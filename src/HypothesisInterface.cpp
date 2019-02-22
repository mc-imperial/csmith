#include "HypothesisInterface.h"

#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define BUF_SIZE 200

static const char *fifo_commands = getenv("HYPOTHESISFIFOCOMMANDS");
static const char *fifo_results = getenv("HYPOTHESISFIFORESULTS");

FILE *results_file = NULL;
FILE *command_file = NULL;

static char incoming[BUF_SIZE];
static char outgoing[BUF_SIZE];

static void writeCommand(const char *command) {
  int fd = open(fifo_commands, O_WRONLY);
  strcpy(outgoing, command);
  write(fd, outgoing, strlen(outgoing) + 1);
  close(fd);
}

static void readResult() {
  if (results_file == NULL)
    results_file = fopen(fifo_results, "r");
  assert(results_file != NULL);
  int i = 0;
  while (true) {
    int c = fgetc(results_file);
    if (c == EOF)
      continue;
    if (c == '\n')
      break;
    assert(i < BUF_SIZE);
    incoming[i++] = c;
  }
  incoming[i] = 0;
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

void hypothesisInitConnection() {}

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
