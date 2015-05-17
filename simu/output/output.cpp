
#include "output.h"
#include <fstream>
#include <sstream>
#include <string>
#include <iostream>

bool writeOutput(char* pcOutput,f1DCalculationContainer const *
		const calculation,float const* const buffer, int param)
{
	if (param<1) param=1;
	//storing output
	std::ofstream output(pcOutput);
    if (!output.is_open()){//create file stream and check it
		std::cout<<"Error while opening file: "<<std::endl;
        std::perror(pcOutput);
		std::cout<<"Berechnung beendet"<<std::endl;
		return false;
	}
	for (unsigned int i=0; i<calculation->info->numberTimesteps;i+=param){
		for (unsigned int j=0; j<calculation->elements.size();j++)
		{
			output<<calculation->elements[j].ID<<'\t';
			output<<calculation->info->dt*float(i)<<'\t';
			output<<buffer[j+calculation->elements.size()*i]<<'\n';
		}
	}

	output.close();


	return true;
}

bool writeOutput(char* pcOutput,f1DMicrophone &microphone)
{
	std::ostringstream  ostr;
	ostr<<pcOutput<<"_m"<<microphone.ID;
	std::string str(ostr.str());
	std::ofstream output(str.c_str());

    if (!output.is_open()){//create file stream and check it
		std::cout<<"Error while opening file: "<<std::endl;
        std::perror(pcOutput);
		std::cout<<"Berechnung beendet"<<std::endl;
		return false;
	}
    microphone.writeToStream(output);

	output.close();
	return true;
}
