//Leapfrog Speakersimulation Project
//Headerfile created by Hendrik Levering
//� Hendrik Levering April 2015

//This header includes the main speaker dgl and functions to load the needed tsp from a file
  // http://www.visaton.de/bilder/forum/tsp-daten-alt.htm für tsp

#ifndef SPEAKER_H
#define SPEAKER_H

#include "simtyps.h" 
#include "errorcodes.h"


#include <iostream>
#include <fstream>
#include <sstream>


bool initializeSpeakers(const char* filename,std::vector<f1DSpeaker> &speakers,pVelocityFunction testsignal);

bool resetspeakers(std::vector<f1DSpeaker> &speakers,pVelocityFunction testsignal);

//This functions loads the values mmd, rms, cms, sd, re, bl, le from a speakerfile

bool loadTSPSet(const char* filename,fSpeakerDescriptor &desc, const int id);//ID =-1 =>first tsp set which is found is used


//This is the main dgl which describes the behaviour of the speaker	, u is the input signal to follow, v and x are updated 
//returns 1 if every thing went well and 0 if an error occured
int speakerdgl (float u,float dt,fSpeakerDescriptor const & desc,float & v,float & x,float & i,float p_left, float p_right, float airmass); // ( input to follow (e.g. voltage) ,dt, fspeakerdesc., v ,x pressureforce left, presscureforce right,airmass

#endif //SPEAKER_H
