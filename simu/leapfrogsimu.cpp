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

	std::ofstream outfile(data.m_strOutputFile);
	outfile<<"<simu_output>\n";


 	for (unsigned int iFreq=0; iFreq<data.m_vfFrequencies.size() ; iFreq++)
 	{
 		float fFreq = data.m_vfFrequencies[iFreq];
 		std::cout << fFreq << " Hz\n";

 		outfile<<"<signal freq = \"" << fFreq << "\" type=\"sin\" >\n";

 		for (unsigned int j=0;j<calculation->microphones.size();j++)
 		{
 			calculation->microphones[j].resetBuffer();
 		}
 		resetspeakers(calculation->speakers,csin);

 		for (unsigned int j=0;j<calculation->elements.size();j++)
 			calculation->elements[j].pressure = 0;

 		for (unsigned int j=0;j<calculation->connectors.size();j++)
			calculation->connectors[j].velocity = 0;

 		for (unsigned int j=0;j<calculation->openElements.size();j++)
 		{
 			calculation->openElements[j].element.pressure = 0;
 			calculation->openElements[j].connector->velocity = 0;
 		}


 		f1DStartCalculation(calculation,buffer, fFreq);

 		for (unsigned int j=0;j<calculation->microphones.size();j++)
 		{
 			std::string strOutFileName = data.m_strOutputFile + calculation->microphones[j].strLabel + std::to_string(iFreq);
 			std::ofstream outFile(strOutFileName);
 			calculation->microphones[j].writeToStream(outFile);

 			outfile<<"<mic_output id = \"" << calculation->microphones[j].strLabel << "\" file = \"" << strOutFileName << "\"/>\n";
 		}

 		for (unsigned int j=0;j<calculation->speakers.size();j++)
 		{
 			std::string strOutFileName = data.m_strOutputFile + std::to_string(calculation->speakers[j].ID) + std::string("_") + std::to_string(iFreq);
			std::ofstream outFile(strOutFileName);
			calculation->speakers[j].monitor.writeToStream(outFile);

			outfile<<"<speaker_output id = \"" << calculation->speakers[j].ID << "\" file = \"" << strOutFileName << "\"/>\n";
 		}

 		std::string strOutFileName = data.m_strOutputFile + std::string("_element") + std::to_string(iFreq);

 		writeOutput(strOutFileName.c_str(),calculation,buffer,20);
 		outfile<<"<element_output file = \"" << strOutFileName << "\"/>\n";

 		outfile<<"</signal>\n";

 		exit(0);

 	}

	std::cout<<"Finish calculation... "<<std::endl;	

	outfile<<"</simu_output>\n";

	delete[] buffer;
	delete calculation->info;
	delete calculation;

	std::cout<<"Berechnung beendet"<<std::endl;

	return 0;
}

