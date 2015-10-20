/*
 * controlfile.h
 *
 *  Created on: 17.10.2015
 *      Author: hendrik
 */

#ifndef CONTROLFILE_H_
#define CONTROLFILE_H_

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

enum signals {sin, delta};

struct cfData{
	std::string element_file;
	float max_timestep;
	int signal_type;
	std::vector<float>  frequencies;
	float signal_periods;
	float trailing_periods;
	std::vector<std::string>speakers;
};

bool loadControlFile(char* filename,cfData &data);




#endif /* CONTROLFILE_H_ */
