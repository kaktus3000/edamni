/*
 * controlfile.h
 *
 *  Created on: 17.10.2015
 *      Author: hendrik
 */

#ifndef CONTROLFILE_H_
#define CONTROLFILE_H_

#include <string>
#include <vector>
#include <map>

enum ESignals
{
	SIG_SINE,
	SIG_DELTA,
	SIG_SQUARE
};

struct cfData{
	//basic info for kernel
	std::string m_strElementFile;
	std::string m_strOutputFile;
	float m_fMaxTimestep;

	//defines signal shape
	ESignals m_SignalType;
	std::vector<float>  m_vfFrequencies;

	unsigned int m_nSignalPeriods;
	unsigned int m_nTrailingPeriods;

	//speaker name -> definition file
	std::map<std::string, std::string> m_Speakers;
};

bool loadControlFile(char* filename,cfData &data);

#endif /* CONTROLFILE_H_ */
