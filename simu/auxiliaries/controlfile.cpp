/*
 * controlfile.cpp
 *
 *  Created on: 17.10.2015
 *      Author: hendrik
 */

#include "controlfile.h"




//end configurationfile structure



bool getLine(std::ifstream &file,std::string &buffer, int &LineInFile){
	if (!std::getline(file,buffer));
		std::cout<<"Unexpected end of File."<<LineInFile<<std::endl;
	LineInFile++;
	if (!buffer.size()){
		std::cout<<"FATAL_ERROR: File could not be read @Line: "<<LineInFile<<std::endl;
		return false;
	}
	return true;
}

bool getDataString(std::string &in, std::string &out, const char* const label){
	std::string buffer; //to read lines from filestream
	std::istringstream parsingBuffer; //To get easy access to typconverting during parsinsg the string buffer
	buffer=in;

	parsingBuffer.str( buffer);
	buffer.clear();
	parsingBuffer>>buffer;
	if (parsingBuffer.fail()){ //und testen
		std::cout<<"Label: "<< label<<" expected!"<<std::endl;
		return false;
	}
	if (buffer!=label)
	{
		std::cout<<"Label: "<< label<<" expected!"<<std::endl;
		return false;
	}
	buffer.clear();
	parsingBuffer>>buffer;

	if (parsingBuffer.fail()){ //und testen
		std::cout<<"Label: </ = /> expected!"<<std::endl;
		return false;
	}
	if (buffer!="=")
	{
		std::cout<<"Label: </ = /> expected!"<<std::endl;
		return false;
	}

	buffer.clear();
	parsingBuffer>>buffer;

	if (parsingBuffer.fail()){ //und testen
        std::perror("Error while reading file!");
		std::cout<<"data expected for "<<label<<std::endl;
		return false;
	}
	out.clear();
	out=buffer;

	return true;
}
std::string trash;

bool getString(std::ifstream &file, int &LineInFile, const char* const label,bool data=false, std::string &out =trash){
	std::string buffer; //to read lines from filestream
	std::string buffer2;

	if(!getLine(file, buffer, LineInFile)) return false;
	if (!data)
	{
	if(!getDataString(buffer,buffer2,label)){
		std::cout<<"Bad File: Error while trying to read data for "<<label<<" @Line: "<<LineInFile<<std::endl;
		return false;
	}
	out=buffer2;
	return true;
	} else
	{
		if(buffer!=label){
			std::cout<<"Bad File: Label "<<label<<" could not be found @Line: "<<LineInFile<<std::endl;
			return false;
		}
		return true;
	}
}

bool getInt(std::ifstream &file, int &LineInFile, const char* const label, int &out){
	std::string buffer; //to read lines from filestream
	std::string buffer2;
	int dummy;
	std::istringstream parsingBuffer; //To get easy access to typconverting during parsinsg the string buffer
	if(!getLine(file, buffer, LineInFile)) return false;

	if(!getDataString(buffer,buffer2,label)){
		std::cout<<"Bad File: Error while trying to read data for "<<label<<" @Line: "<<LineInFile<<std::endl;
	}
	parsingBuffer.str(buffer2);
	parsingBuffer>>dummy;

	if (parsingBuffer.fail()){ //und testen
        std::perror("Error while reading file!");
		std::cout<<"Integer expected for data  "<<label<<" @Line: "<<LineInFile<<std::endl;
		return false;
	}
	out =dummy;
	return true;
}

bool getFloat(std::ifstream &file, int &LineInFile, const char* const label, float &out){
	std::string buffer; //to read lines from filestream
	std::string buffer2;
	float dummy;
	std::istringstream parsingBuffer; //To get easy access to typconverting during parsinsg the string buffer
	if(!getLine(file, buffer, LineInFile)) return false;

	if(!getDataString(buffer,buffer2,label)){
		std::cout<<"Bad File: Error while trying to read data for "<<label<<" @Line: "<<LineInFile<<std::endl;
	}
	parsingBuffer.str(buffer2);
	parsingBuffer>>dummy;

	if (parsingBuffer.fail()){ //und testen
        std::perror("Error while reading file!");
		std::cout<<"Float expected for data  "<<label<<" @Line: "<<LineInFile<<std::endl;
		return false;
	}
	out =dummy;
	return true;
}

bool getSignalType(std::ifstream &file, int &LineInFile, const char* const label, int &out){
	std::string buffer;
	if (!getString(file,LineInFile,"signal_type",true,buffer)) return false;
	if (buffer=="sin"){
		out = sin;
		return true;
	}
	if (buffer=="delta"){
		out = delta;
		return true;
	}
	std::cout<<"Bad File: Unknown signal typ: "<<buffer<<" found @Line: "<<std::endl;
}



bool loadControlFile(char* filename,cfData &data)
{
	std::cout<<"Load configuration-file: "<<filename<<std::endl;

	std::ifstream file(filename,std::ios_base::in);
    if (!file.is_open()){
		std::cout<<"Error while opening file: "<<std::endl;
        std::perror(filename);
		return false; //create file stream and check it
	}

    int LineInFile=0;

	if (!getString(file,LineInFile,"[general]")) return false;
	if (!getString(file,LineInFile,"element_file",true,data.element_file)) return false;
	if (!getFloat(file,LineInFile,"max_timestep",data.max_timestep)) return false;
	if (!getString(file,LineInFile,"")); //Leerzeile übergehen
	if (!getSignalType(file,LineInFile,"signal_type",data.signal_type)) return false;

	return true;
}
