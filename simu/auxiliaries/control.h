/*
 * control.h
 *
 *  Created on: 17.10.2015
 *      Author: hendrik
 */

#ifndef CONTROL_H_
#define CONTROL_H_




struct programControl{
	char* configPath;
	bool opt1;
	bool opt2;
	bool opt3;
};


bool readParam(int argc, char* argv[], programControl &pControl);




#endif /* CONTROL_H_ */
