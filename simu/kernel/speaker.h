//Leapfrog Speakersimulation Project
//Headerfile created by Hendrik Levering
//© Hendrik Levering April 2015

//This header includes the main speaker dgl


#ifndef SPEAKER_H
#define SPEAKER_H

#include "simtyps.h" 



//This is the main dgl which describes the behaviour of the speaker	, u is the input signal to follow, v and x are updated 
//returns 1 if every thing went well and 0 if an error occured
int speakerdgl (float u,float dt,fSpeakerDescriptor const & desc,float & v,float & x,float & i,float p_left, float p_right, float airmass); // ( input to follow (e.g. voltage) ,dt, fspeakerdesc., v ,x pressureforce left, presscureforce right,airmass

#endif //SPEAKER_H