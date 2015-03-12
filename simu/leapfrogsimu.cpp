// leapfrogsimu.cpp : Definiert den Einstiegspunkt f�r die Konsolenanwendung.
//

#include <iostream>
#include <sstream>
//#include <Windows.h>
#include <string>
#include <fstream>


#include "kernel/simtyps.h"
//#include "bitmap.h"
#include "kernel/kernelaux.h"
#include "tests/testfunction.h"
#include "kernel/core1d.h"

int
main(int argc, char* argv[])
{

	f1DCalculationContainer* testCalculation=new f1DCalculationContainer;
	testCalculation->info= new f1DCalculationDescriptor;

	useDefaultDescriptor(testCalculation->info);
	load1DKernelInput("horn.elems.txt",testCalculation);

	//assigned speaker functions and init speakers
	for(unsigned int i=0; i<testCalculation->speakers.size();i++)
	{
		testCalculation->speakers[i].f=&tsin2;
		testCalculation->speakers[i].airmass=0.0f;
		testCalculation->speakers[i].speakerDiscriptor=nullptr;
		testCalculation->speakers[i].v=0.0f;
	}

	//reserve memory for storing results
	float* buffer= new float[testCalculation->elements.size()*testCalculation->info->numberTimesteps];
	//do calculation
	std::cout<<"Start calculation... "<<std::endl;
	f1DStartCalculation(testCalculation,buffer);
	std::cout<<"Finish calculation... "<<std::endl;	
	std::cout<<"Storing results... "<<std::endl;
	std::ofstream output("output.txt");
    if (!output.is_open()){//create file stream and check it
		std::cout<<"Error while opening file: "<<std::endl;
        std::perror("output.txt");
		std::cout<<"Berechnung beendet"<<std::endl;
		std::cin.get();
		return 0; 
	}
	output<<"<ID> <tab> <timestep> <tab> <pressure> <newline>"<<std::endl;

	for (unsigned int i=0; i<testCalculation->info->numberTimesteps;i++){
		for (unsigned int j=0; j<testCalculation->elements.size();j++)
		{
			output<<testCalculation->elements[j].ID<<'\t';
			output<<testCalculation->info->dt*float(i)<<'\t';
			output<<buffer[j+testCalculation->elements.size()*i]<<'\n';
		}
	}

	output.close();
	
	delete[] buffer;
	delete testCalculation->info;
	delete testCalculation;



	std::cout<<"Berechnung beendet"<<std::endl;
	std::cin.get();

	return 0;
}

