//Leapfrog Speakersimulation Project
//Headerfile created by Hendrik Levering
//� Hendrik Levering Februar 2015
//� Hendrik Levering Februar 2015, all rights reserved


//This headerfile includes signal testfunctions for the simulation
#ifndef TESTFUNCTIONS_H
#define TESTFUNCTIONS_H

#include "../kernel/simtyps.h"

// (only dt is needed) returns 1 if dt==0 else 0 is returned
float deltaimpuls (float dt,fSpeakerDiscriptor* desc,float v_old, float p_minus, float p_plus, float airmass); 

float tsin (float dt,fSpeakerDiscriptor* desc,float v_old, float p_minus, float p_plus, float airmass);


float tsin2 (float dt,fSpeakerDiscriptor* desc,float v_old, float p_minus, float p_plus, float airmass);

#endif
