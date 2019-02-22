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


static void writeOutgoing(){
  FILE *fd = fopen(fifo_commands, "w");
  int n = strlen(outgoing);
  assert(n < 256);
  fputc(n, fd);
  fwrite(outgoing, sizeof(char), strlen(outgoing), fd);
  fclose(fd);
}

static void writeCommand(const char *command) {
  strcpy(outgoing, command);
  writeOutgoing();
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
  sprintf(outgoing, "START %s", label);
  assert(strlen(outgoing) > 0);
  writeOutgoing();
  getAck();
}

void hypothesisEndExample() {
  writeCommand("END");
  getAck();
}
