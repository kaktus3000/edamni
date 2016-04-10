#include "speaker.h"
//this is a speaker model.

#include <iostream>
#include <fstream>
#include "../input/scanINI.h"

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
	//desc.resitanceMass=desc.resitanceMass;

	return true;
}

bool loadTSPSet(const char* filename,fSpeakerDescriptor &desc, const int id)
{
	std::cout<<"Load speaker file: "<<filename<<std::endl;

	std::ifstream file(filename,std::ios_base::in);
    if (!file.is_open()){
		std::cout<<"Error while opening file: "<<std::endl;
        std::perror(filename);
		return false; //create file stream and check it
	}

	try
    {
		ScanINI speakerConfig(file);

		desc.DCResistance = std::stof(speakerConfig.getKey("tspset", "re") );
		desc.bl = std::stof(speakerConfig.getKey("tspset", "bl") );
		desc.inductance = std::stof(speakerConfig.getKey("tspset", "le") );
		desc.mass = std::stof(speakerConfig.getKey("tspset", "mmd") );
		desc.resitanceMass = std::stof(speakerConfig.getKey("tspset", "re") );
		desc.sd = std::stof(speakerConfig.getKey("tspset", "sd") );
		desc.springForce = std::stof(speakerConfig.getKey("tspset", "cms") );

    }
    catch (std::exception& e) {
    	std::cout<<"Fehler beim Parsen der TSP-Daten gefunden für ID: "<<id<<"\n";
    	return false;
	}

	if (id>=0) //look for tspdata with ID =id
	{
		if (!checkTSPSet(desc))
		{
			std::cout<<"Fehlerhafte TSP-Daten gefunden für ID: "<<id<<"\n";
			return false;
		}
		if (!convertTSP(desc))
		{
			std::cout<<"Fehler beim konvertieren der TSP Daten!\n";
			return false;
		}
		return true;

	}

	std::cout<<"ID muss >=0 sein! ID: "<<id<<"\n";
	return false;
}

bool initializeSpeakers(const char* filename,std::vector<f1DSpeaker> &speakers,pVelocityFunction testsignal, f1DCalculationDescriptor  const &desc)
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

		speakers[i].position->crossSectionArea=speakers[i].speakerDescriptor.sd;
		//speakers[i].position2->crossSectionArea=speakers[i].speakerDescriptor.sd;
		speakers[i].monitor.initialize(speakers[i].ID,desc.numberTimesteps,desc.dt);
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

	i= (u-desc.bl*v+desc.inductance*i/dt)/(desc.DCResistance+desc.inductance/dt);
	//float iind= (-desc.bl*v-desc.resitanceMass*i)/desc.resitanceMass; //inductive current
	float forceMembran=desc.bl*i;
	float a=(+forceMembran+(p_left-p_right)*desc.sd-x*desc.springForce-desc.resitanceMass*u/desc.bl)/(desc.mass+airmass);
	v=v+a*dt;
	//v=0;
	x=x+v*dt;
	//std::cout<<"U: "<<u<<" I: "<<i<<" v: "<<v<<" x: "<<x<<std::endl;


	return 1;
}
