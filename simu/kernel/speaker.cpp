#include "speaker.h"
//this is a speaker model.



//auxilary function for load speaker TSP
// needs a tsp label and a corrosponding tsp value
// value is correctly stored in speaker
// returns if an error occurs
bool storeData( std::string const &label, const float value,fSpeakerDescriptor &desc)
{
	if (value <=0) return false;

	if ((label == "le")||(label=="LE"))
	{
		desc.inductance=value;
		return true;
	}


	if ((label == "rms")||(label=="RMS"))
	{
		desc.resitanceMass=value;
		return true;
	}

	if ((label == "bl")||(label=="BL"))
	{
		desc.bl = value;
		return true;
	}

	if ((label == "cms")||(label=="CMS"))
	{
		desc.springForce = value;
		return true;
	}

	if ((label == "sd")||(label=="SD"))
	{
		desc.sd=value;
		return true;
	}

	if ((label == "re")||(label=="RE"))
	{
		desc.DCResistance=value;
		return true;
	}

	if ((label == "mmd")||(label=="MMD"))
	{
		desc.mass=value;
		return true;
	}

	return true; //there was an undefined label // can be set to return true, if this case shall be ignored
}

//check if every needed tsp data is there
bool checkTSPSet(fSpeakerDescriptor &desc)
{
	if( desc.DCResistance<=0) return false;
	if( desc.bl<=0) return false;
	if( desc.inductance<=0) return false;
	if( desc.mass<=0) return false;
	if( desc.resitanceMass<=0) return false;
	if( desc.sd<=0) return false;
	if( desc.springForce<=0) return false;
	return true;
}

//convert tsp to mechanical values which are needed by kernel
bool convertTSP(fSpeakerDescriptor &desc)
{
	if( desc.resitanceMass<=0) return false;
	if( desc.bl<=0) return false;
	if( desc.springForce<=0) return false;

	desc.springForce=1.0f/desc.springForce;
	desc.resitanceMass=desc.bl*desc.bl/desc.resitanceMass;

	return true;
}


bool convertLine(std::string const &buffer,std::string &labelDummy,float &value,bool param=false)//param=true => read only the label
{
	std::istringstream parsingBuffer; //To get easy access to type converting during parsing the string buffer
	parsingBuffer.str(buffer);

	//read the label
	parsingBuffer>>labelDummy;
	if (parsingBuffer.fail()){ //und testen
		labelDummy="";
		value=-1.0f;
		return false;
	}

	if (param) return true; //return if value is not needed

	//read value
	parsingBuffer>>value;
	if (parsingBuffer.fail()){ //und testen
		value=-1.0f;
		return false;
	}
	return true;// everything went fine
}

int f2i(float f)
{
  return f<0?f-.5:f+.5;
}

bool loadTSPSet(const char* filename,fSpeakerDescriptor &desc, const int id)
{
	float value = -1.0f;
	int LineInFile=0; //Gives the current line for debugging reason
	bool idFound=false;
	std::string labelDummy;
	std::string buffer; //to read lines from a file stream

	std::cout<<"Load TSP data..."<<std::endl;

	std::ifstream file(filename,std::ios_base::in);
    if (!file.is_open()){
		std::cout<<"Error while opening file: "<<std::endl;
        std::perror(filename);
		return false; //create file stream and check it
	}

	if(!std::getline(file,buffer)){
		std::cout<<"File is Empty!"<<std::endl;
		return false;
	}
	LineInFile++;


	convertLine(buffer,labelDummy,value);
	buffer.clear();
	if( labelDummy!="TSPSET")
	{
		std::cout<<"Unexpected File Found. Label <TSPSET> expected @Line: "<<LineInFile<<std::endl;
		return false;
	}
	if (id>=0) //look for tspdata with ID =id
	{
		if(f2i(value)!=id)
		{
			while (!idFound)
			{
				if(!std::getline(file,buffer))
				{
					std::cout<<"TSPSet with ID: "<<id<<" could not be found!"<<std::endl;
					return false;
				}
				LineInFile++;
				convertLine(buffer,labelDummy,value);
				if ((f2i(value)==id)&&(labelDummy=="TSPSET"))
				{
					idFound=true;
				}
				buffer.clear();
			}
		}
		labelDummy="";
		while (labelDummy!="TSPSET")
		{
			if(!std::getline(file,buffer))
			{
				buffer.clear();
				break;//Fehler beim Lesen der Datei oder Dateiende
			}
			LineInFile++;
			convertLine(buffer,labelDummy,value);
			storeData(labelDummy,value,desc);
		}
		if (!checkTSPSet(desc))
		{
			std::cout<<"Fehlerhafte TSP-Daten gefunden für ID: "<<id<<" @Line: "<<LineInFile<<std::endl;
			return false;
		}
		if (!convertTSP(desc))
		{
			std::cout<<"Fehler beim konvertieren der TSP Daten! @Line: "<<LineInFile<<std::endl;
			return false;
		}
		return true;

	}

	std::cout<<"ID muss >=0 sein! ID: "<<id<<" @line: "<<LineInFile<<std::endl;
	return false;


}

bool initializeSpeakers(const char* filename,std::vector<f1DSpeaker> &speakers,pVelocityFunction testsignal)
{
	if (testsignal==0)
	{
		std::cout<<"Bad test function pointer found while initializing driver!"<<std::endl;
		return false;
	}
	for(unsigned int i=0; i<speakers.size();i++)
	{
		speakers[i].reset(testsignal);
		speakers[i].airmass=0.0f;
		if (!loadTSPSet(filename,speakers[i].speakerDescriptor,0)) return false;
	}
	return true;
}

bool resetspeakers(std::vector<f1DSpeaker> &speakers,pVelocityFunction testsignal)
{
	if (testsignal==0)
	{
		std::cout<<"Bad test function pointer found while reseting drivers!"<<std::endl;
		return false;
	}
	for(unsigned int i=0; i<speakers.size();i++)
	{
		speakers[i].reset(testsignal);
	}
	return true;

}


int speakerdgl (float u,float dt,fSpeakerDescriptor const & desc,float & v,float & x,float & i,float p_left, float p_right, float airmass) // ( input to follow (e.g. voltage) ,dt, fspeakerdesc., v ,x, i amplifier current, pressureforce left, presscureforce right,airmass
{
	if( dt==0) return 1; //Null Zeitschritt = keine �nderung
	if( desc.DCResistance==0) return 0;
	if( desc.sd==0) return 0;
	if( desc.inductance==0) return 0;
	if( desc.resitanceMass==0) return 0;
	if( desc.springForce==0) return 0;
	if( desc.bl==0) return 0;
	if( desc.mass==0) return 0;

	i= (u+desc.bl*v+desc.inductance*i/dt)/(desc.DCResistance+desc.inductance/dt);
	float iind= (-desc.bl*v-desc.resitanceMass*i)/desc.resitanceMass; //inductive current
	float forceMembran=desc.bl*iind;
	float a=(forceMembran+(p_left-p_right)*desc.sd-x*desc.springForce)/(desc.mass+airmass);

	x=x+v*dt;
	v=v+a*dt;

	return 1;
}
