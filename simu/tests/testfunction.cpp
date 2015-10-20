
#include "testfunction.h"

#define _USE_MATH_DEFINES

#include <math.h>


#include "../kernel/speaker.h"
#include "../kernel/simtyps.h"

float deltaimpuls (float dt,f1DSpeaker & speaker,float param,bool reset)
{
	//static float elapsedTime=0;
	if (reset)
	{
		speaker.i=0;
		speaker.v=0;
		speaker.x=0;
		//elapsedTime=0;

		if (speakerdgl (VOLTAGE_DEFAULT/dt,dt,speaker.speakerDescriptor,speaker.v,speaker.x,speaker.i,speaker.speakerDescriptor.sd*speaker.position->positiveNeighbour->pressure, speaker.speakerDescriptor.sd*speaker.position2->negativeNeighbour->pressure, speaker.airmass))
			return speaker.v;
		else
			return 0.0f;
	}

	if (speakerdgl (0,dt,speaker.speakerDescriptor,speaker.v,speaker.x,speaker.i,speaker.speakerDescriptor.sd*speaker.position->positiveNeighbour->pressure, speaker.speakerDescriptor.sd*speaker.position2->negativeNeighbour->pressure, speaker.airmass))
		return speaker.v;
	else
		return 0.0f;
}

float csin (float dt,f1DSpeaker & speaker,float param,bool reset)
{
	static float elapsedTime=0;
	if (reset) elapsedTime=0;
	float voltage=0;

	const float w=param*2.0f*M_PI;

	voltage=sin(w*elapsedTime)*VOLTAGE_DEFAULT;
	speaker.storeStatus(voltage);
	elapsedTime+=dt;
	if (speakerdgl (voltage,dt,speaker.speakerDescriptor,speaker.v,speaker.x,speaker.i,speaker.speakerDescriptor.sd*speaker.position->positiveNeighbour->pressure, speaker.speakerDescriptor.sd*speaker.position2->negativeNeighbour->pressure, speaker.airmass))
		return speaker.v;
		return 0.0f;
}

float hdeltaimpuls (float dt,f1DSpeaker & speaker,float param,bool reset)
{
	if (reset)
		return VOLTAGE_DEFAULT/dt;
	return 0.0f;
}

float hcsin (float dt,f1DSpeaker & speaker,float param,bool reset)
{
	static float elapsedTime=0;
	if (reset) elapsedTime=0;
	float dummy=0;

	const float w=param*2.0f*M_PI;
	dummy=sin(w*elapsedTime);
	elapsedTime+=dt;

	return dummy;
}

float hcsin2 (float dt,f1DSpeaker & speaker,float param,bool reset)
{
	static float elapsedTime=0;
	if (reset) elapsedTime=0;
	float dummy=0;

	const float w=param*2.0f*M_PI;
	dummy=sin(w*elapsedTime)*VOLTAGE_DEFAULT;
	dummy*=dummy;
	elapsedTime+=dt;
	return dummy;
}

float hssin2 (float dt,f1DSpeaker & speaker,float param,bool reset)
{
	static float elapsedTime=0;
	if (reset) elapsedTime=0;
	float dummy=0;

	const float w=param*2.0*M_PI;
	dummy=sin(w*elapsedTime)*VOLTAGE_DEFAULT;
	dummy*=dummy;
	elapsedTime+=dt;
	if (elapsedTime>(0.5f/param)) return 0.0f;
	return dummy;
}
