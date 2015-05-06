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
#include <limits> 

int
main(int argc, char* argv[])
{

	f1DCalculationContainer* testCalculation=new f1DCalculationContainer;
	testCalculation->info= new f1DCalculationDescriptor;

	useDefaultDescriptor(testCalculation->info);

	char* input= new char[100];

	std::cout<<"please enter the filename of an element list..."<<std::endl;	
	std::cin>>input;
    std::cin.clear();
    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');

	if (load1DKernelInput(input,testCalculation)!=NO_ERR) 
	{
		std::cout<<"Press any key to quit calculation..."<<std::endl;
		std::cin.get();
		return 0;
	}

	//assigned speaker functions and init speakers
	for(unsigned int i=0; i<testCalculation->speakers.size();i++)
	{
		testCalculation->speakers[i].f=&deltaimpuls;
		testCalculation->speakers[i].airmass=0.0f;
		testCalculation->speakers[i].speakerDescriptor.bl=20.0f;
		testCalculation->speakers[i].speakerDescriptor.damping=1.0f;
		testCalculation->speakers[i].speakerDescriptor.DCResistance=5.4f;
		testCalculation->speakers[i].speakerDescriptor.inductance=1.4f;
		testCalculation->speakers[i].speakerDescriptor.mass=0.143f;
		testCalculation->speakers[i].speakerDescriptor.resitanceMass=0.1f;
		testCalculation->speakers[i].speakerDescriptor.springForce=1.0f;
		testCalculation->speakers[i].v=0.0f;
		testCalculation->speakers[i].x=0.0f;
		testCalculation->speakers[i].i=0.0f;
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

