#ifndef HYPOTHESIS_INTERFACE
#define HYPOTHESIS_INTERFACE

void hypothesisBeginInterval();

void hypothesisEndInterval();

void hypothesisInitConnection();

void hypothesisTerminateConnection();
void hypothesisStartExample();
void hypothesisEndExample();

unsigned long hypothesisGetRand();

#define HYPOTHESIS_DRAW(cls, args...) ({  hypothesisStartExample(); auto result = cls::make_random(args); hypothesisEndExample(); result })
#endif //HYPOTHESIS_INTERFACE
