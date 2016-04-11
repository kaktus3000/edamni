// leapfrogsimu.cpp : Definiert den Einstiegspunkt f�r die Konsolenanwendung.
//

//include standard libraries
#include <iostream>
#include <sstream>
//#include <Windows.h>
#include <string>
#include <fstream>
#include <limits>

//include custom libraries
#include "auxiliaries/incaux.h"
#include "kernel/kernelinc.h"


#include "tests/testfunction.h"

#include "output/output.h"
#include "output/postprocessing.h"


#include "input/scanINI.h"

int
main(int argc, char* argv[])
{
	puts("test");
	programControl pControl;


	if (!readParam(argc, argv, pControl)) return -1; //read programm controlling parameters

	cfData data;

	if(!loadControlFile(pControl.configPath, data))
	{
		std::cout<<"ERROR parsing simulation control file. Shutting down.\n";
		return -1;
	}

	int error;

	f1DCalculationContainer* calculation=new f1DCalculationContainer;
	calculation->info= new f1DCalculationDescriptor;

	useDefaultDescriptor(calculation->info);

	if ((error=load1DKernelInput(data.m_strElementFile.c_str(), calculation))!=NO_ERR)
	{
		std::cout<<"An Error occurred during parsing geometry to kernel format. ErrorCode = "<<error<<std::endl;
		return -1;
	}


	if(!initializeSpeakers(data.m_Speakers.begin()->second.c_str(),calculation->speakers,csin,calculation->info[0]))
	{
		std::cout<<"An Error occurred during initializing drivers"<<std::endl;
		return -1;
	}

	preCalculate(calculation);

	//reserve memory for storing results
	float* buffer= new float[calculation->elements.size()*calculation->info->numberTimesteps];

	//do calculation
	std::cout<<"Start calculation... "<<std::endl;

	frequencyOutput* frequencyData= new frequencyOutput[calculation->microphones.size()];


	frequencyOutput* frequencyRmsData= new frequencyOutput[calculation->speakers.size()];

 	for (unsigned int iFreq=0; iFreq<data.m_vfFrequencies.size() ; iFreq++)
 	{
 		float fFreq = data.m_vfFrequencies[iFreq];
 		std::cout << fFreq << " Hz\n";

 		for (unsigned int j=0;j<calculation->microphones.size();j++)
 		{
 			calculation->microphones[j].resetBuffer();
 		}
 		resetspeakers(calculation->speakers,csin);

 		f1DStartCalculation(calculation,buffer, fFreq);
 		float k1,k2,k3;
 		for (unsigned int j=0;j<calculation->microphones.size();j++)
 		{
 			frequencyData[j].storeData(fFreq , getAmplitude(calculation->microphones[j],k1,k2,k3,STEPSTOIGNORE));
 			//calculation->microphones[j].resetBuffer();
 		}

 		for (unsigned int j=0;j<calculation->speakers.size();j++)
 		{
 			frequencyRmsData[j].storeData(fFreq, getRMS(calculation->speakers[j].monitor,STEPSTOIGNORE));
 		}

 	}

 	std::string strOut = std::string(pControl.configPath) + std::string("out");

	for (unsigned int j=0;j<calculation->microphones.size();j++)
	{
		writeOutput(strOut.c_str(),frequencyData[j],calculation->microphones[j].strLabel);
	}
	for (unsigned int j=0;j<calculation->speakers.size();j++)
	{
		writeRms(strOut.c_str(),frequencyRmsData[j],calculation->speakers[j].ID);
	}
	std::cout<<"Finish calculation... "<<std::endl;	
	std::cout<<"Storing results... "<<std::endl;

	std::ofstream outfile(data.m_strOutputFile);




	writeOutput(strOut.c_str(),calculation,buffer,20);

	delete[] frequencyData;
	delete[] buffer;
	delete calculation->info;
	delete calculation;

	std::cout<<"Berechnung beendet"<<std::endl;

	return 0;
}

