

//This headerfile includes functions to store calculated results in a file

#ifndef OUTPUT_H
#define OUTPUT_H

#include "../kernel/simtyps.h"

bool writeOutput(char* pcOutput,f1DCalculationContainer const *const Calculation,float const* const buffer,int param =1);

bool writeOutput(char* pcOutput,f1DMicrophone  &microphone);

bool writeOutput(char* pcOutput,frequencyOutput  &data,int ID=0);

bool writeRms(char* pcOutput,frequencyOutput  &data,int ID=0);

#endif
