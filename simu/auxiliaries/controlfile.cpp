/*
 * controlfile.cpp
 *
 *  Created on: 17.10.2015
 *      Author: hendrik
 */

#include "controlfile.h"
#include "../input/scanINI.h"

#include <iostream>
#include <fstream>

//end configurationfile structure


bool loadControlFile(char* filename, cfData &data)
{
	std::cout<<"Load configuration-file: "<<filename<<std::endl;

	std::ifstream file(filename,std::ios_base::in);
    if (!file.is_open()){
		std::cout<<"Error while opening file: "<<std::endl;
        std::perror(filename);
		return false; //create file stream and check it
	}

    ScanINI ini(file);

    try
    {
		if(!(data.m_strElementFile = ini.getKey("general", "element_file")).length())
			return false;

		data.m_fMaxTimestep = std::stof(ini.getKey("general", "max_timestep"));

		std::string strSignal(ini.getKey("signal", "signal_type"));

		if(strSignal == std::string("sine"))
			data.m_SignalType = SIG_SINE;
		else if(strSignal == std::string("delta"))
			data.m_SignalType = SIG_DELTA;
		else if(strSignal == std::string("square"))
			data.m_SignalType = SIG_SQUARE;

		std::string strFreqs(ini.getKey("signal", "frequencies"));

		size_t pos = 0;
		while((pos = strFreqs.find_first_of(';')) != std::string::npos)
		{
			//cut first frequency off string and convert
			std::string strFreq = strFreqs.substr(0, pos);
			data.m_vfFrequencies.push_back(std::stof(strFreq));
			//truncate string for next iteration
			strFreqs = strFreqs.substr(pos + 1);
		}

		data.m_nSignalPeriods = std::stoi(ini.getKey("signal", "signal_periods"));
		data.m_nTrailingPeriods = std::stoi(ini.getKey("signal", "trailing_periods"));

		//load all speaker names present
		const std::set<std::string> sSpeakers(ini.getKeys("speakers"));
		for(std::set<std::string>::const_iterator it = sSpeakers.begin(); it != sSpeakers.end(); it++)
			data.m_Speakers[*it] = ini.getKey("speakers", *it);

    }
    catch (std::exception& e) {
    	return false;
	}

	return true;
}
