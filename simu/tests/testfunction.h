//Leapfrog Speakersimulation Project
//Headerfile created by Hendrik Levering
//� Hendrik Levering Februar 2015
//� Hendrik Levering Februar 2015, all rights reserved


//This headerfile includes signal testfunctions for the simulation
#ifndef TESTFUNCTIONS_H
#define TESTFUNCTIONS_H

#include "../kernel/simtyps.h"




//schematic names
// h= hard function which will use fixed velocitys and do not regard speaker dgl
// c= contionious loop;
// s= single wave

float deltaimpuls (float dt,f1DSpeaker & speaker,int param=0,bool reset=false);//param = impulse duration in timesteps+1, reset will reset the function to t=0;


float hdeltaimpuls (float dt,f1DSpeaker & speaker,int param,bool reset=false);  //param is not needed, reset will reset the function to t=0;

float hcsin (float dt,f1DSpeaker & speaker,int param,bool reset=false); //continous sin wave ,param = frequence


float hcsin2 (float dt,f1DSpeaker & speaker,int param,bool reset=false); //continous sin² wave ,param = frequence

float hssin2 (float dt,f1DSpeaker & speaker,int param,bool reset=false); //single sin² wave ,param = frequence
#endif
