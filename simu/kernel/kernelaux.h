//Leapfrog Speakersimulation Project
//Headerfile created by Hendrik Levering
//� Hendrik Levering Februar 2015
//� Hendrik Levering Februar 2015, all rights reserved


//This headerfile includes functions to create kernel data from a parsed element list


//To do:
/****************************


map speaker to v-connection: if there is already a connection which is overide with the speaker than

calculate p-factors

*************************/

#ifndef KERNELAUX_H
#define KERNELAUX_H


#include <iostream>                             
#include <fstream>  
#include <sstream>
#include <string>
#include <vector>

#include "simtyps.h"
#include "errorcodes.h"

//initialize the descriptor with default values
int useDefaultDescriptor(f1DCalculationDescriptor* desc);

int load1DKernelInput(const char* filename, f1DCalculationContainer* container,int param=0); //filename file with parsed elements, pointer to container to store data

int checkKernelInput(f1DCalculationContainer* container);

int preCalculate(f1DCalculationContainer* container, int param=0);

#define nullptr 0


#endif
