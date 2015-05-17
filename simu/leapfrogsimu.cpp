// leapfrogsimu.cpp : Definiert den Einstiegspunkt f�r die Konsolenanwendung.
//

#include <iostream>
#include <sstream>
//#include <Windows.h>
#include <string>
#include <fstream>
#include <limits>

#include "kernel/simtyps.h"
//#include "bitmap.h"
#include "kernel/kernelaux.h"
#include "tests/testfunction.h"
#include "kernel/core1d.h"
#include "kernel/speaker.h"
#include "output/output.h"






int
main(int argc, char* argv[])
{
	if(argc < 4)
	{
		puts("give argument, nap!");
		return -1;
	}
	char* pcConfig = argv[1];
	char* pcTSP = argv[2];
	char* pcOutput = argv[3];
	int error;

	f1DCalculationContainer* calculation=new f1DCalculationContainer;
	calculation->info= new f1DCalculationDescriptor;

	useDefaultDescriptor(calculation->info);

	if ((error=load1DKernelInput(pcConfig,calculation))!=NO_ERR)
	{
		std::cout<<"An Error occurred during parsing geometry to kernel format. ErrorCode = "<<error<<std::endl;
		return -1;
	}

	if(!initializeSpeakers(pcTSP,calculation->speakers,deltaimpuls))
	{
		std::cout<<"An Error occurred during initializing drivers"<<std::endl;
		return -1;
	}

	//reserve memory for storing results
	float* buffer= new float[calculation->elements.size()*calculation->info->numberTimesteps];

	//do calculation
	std::cout<<"Start calculation... "<<std::endl;
	f1DStartCalculation(calculation,buffer,20); //500 frequency

	std::cout<<"Finish calculation... "<<std::endl;	
	std::cout<<"Storing results... "<<std::endl;

	writeOutput( pcOutput,calculation,buffer,5);
	for (int i=0;i<calculation->microphones.size();i++)
	{
		writeOutput( pcOutput,calculation->microphones[i]);
	}
	
	delete[] buffer;
	delete calculation->info;
	delete calculation;

	std::cout<<"Berechnung beendet"<<std::endl;

	return 0;
}

