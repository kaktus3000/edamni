

//This headerfile includes functions to store calculated results in a file

#ifndef OUTPUT_H
#define OUTPUT_H

#include "../kernel/simtyps.h"

bool writeOutput(const char* pcOutput,f1DCalculationContainer const *const Calculation,float const* const buffer,int param =1);

bool writeOutput(const char* pcOutput,f1DMicrophone  &microphone);

bool writeOutput(const char* pcOutput,frequencyOutput  &data,std::string& strID);

bool writeRms(const char* pcOutput,frequencyOutput  &data,int ID=0);

#endif
