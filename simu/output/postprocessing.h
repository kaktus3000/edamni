#ifndef POSTPROCESSING_H
#define POSTPROCESSING_H

#include "../kernel/simtyps.h"

float getAmplitude(f1DMicrophone & data,float & k1,float & k2,float & k3,int ignoresteps=500);

float getRMS(f1DSpeakerMonitor & data,int ignoresteps=500);

float getImpedanz(f1DSpeakerMonitor & data,int ignoresteps);


#endif
