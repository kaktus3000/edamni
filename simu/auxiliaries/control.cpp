/*
 * control.cpp
 *
 *  Created on: 17.10.2015
 *      Author: hendrik
 */

#include "control.h"

#include <iostream>
#include <string>

bool checkParam(programControl & pControl)
{
	// to do: include parameter checking
	return true;
}

bool readParam(int argc, char* argv[], programControl &pControl)
{
	pControl.configPath = 0;
	pControl.opt1 = false;
	pControl.opt2 = false;
	pControl.opt3 = false;

	if(argc < 2) //input param checking, too little parameters
	{
		std::cout<<"Error: Missing arguments!"<<std::endl;
		std::cout<<"Correct syntax is:"<<std::endl;
		std::cout<<"edamni <inputconfigfile> [-opt1] [-opt2]..."<<std::endl;
		return false;
	}

	pControl.configPath = argv[1];

	for (int i =0;i<argc; i++){
		std::cout<<i<<"  "<<argv[i]<<std::endl;
	}
	std::cout<<std::endl;



	for (int i =2;i<argc; i++){
		std::string str(argv[i]);
		if (str == "-opt1"){
			if (pControl.opt1 )
			{
				std::cout<<"Warning: Multiply use of parameter:"<<std::endl;
				std::cout<<argv[i]<<std::endl;
			}
			pControl.opt1 =true;
			continue;
		}
		if (str == "-opt2"){
			if (pControl.opt2 )
			{
				std::cout<<"Warning: Multiply use of parameter:"<<std::endl;
				std::cout<<argv[i]<<std::endl;
			}
			pControl.opt2 =true;
			continue;
		}
		if (str == "-opt3"){
			if (pControl.opt3 )
			{
				std::cout<<"Warning: Multiply use of parameter:"<<std::endl;
				std::cout<<argv[i]<<std::endl;
			}
			pControl.opt3 =true;
			continue;
		}
		std::cout<<"Error: Bad parameter:"<<std::endl;
		std::cout<<argv[i]<<std::endl;
		std::cout<<"Correct syntax is:"<<std::endl;
		std::cout<<"edamni <inputConfigFileName> [-opt1] [-opt2]..."<<std::endl;
		return false;
	}

	if (!checkParam(pControl)) return false;

	return true;

}




