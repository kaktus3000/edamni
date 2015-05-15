
#include "testfunction.h"

#define _USE_MATH_DEFINES

#include <math.h>
#include "../kernel/speaker.h"


float deltaimpuls (float dt,f1DSpeaker & speaker,int param,bool reset)
{
	static float elapsedTime=0;
	if (reset)
	{
		speaker.i=0;
		speaker.v=0;
		speaker.x=0;
		elapsedTime=0;

		if (speakerdgl (1,dt,speaker.speakerDescriptor,speaker.v,speaker.x,speaker.i,speaker.position->crossSectionArea*speaker.position->negativeNeighbour->pressure, speaker.position->crossSectionArea*speaker.position->positiveNeighbour->pressure, speaker.airmass))
			return speaker.v;
		else
			return 0.0f;
	}

	if (speakerdgl (0,dt,speaker.speakerDescriptor,speaker.v,speaker.x,speaker.i,speaker.position->crossSectionArea*speaker.position->negativeNeighbour->pressure, speaker.position->crossSectionArea*speaker.position->positiveNeighbour->pressure, speaker.airmass))
			return speaker.v;
	else
		return 0.0f;
}

float csin (float dt,f1DSpeaker & speaker,int param,bool reset)
{
	static float elapsedTime=0;
	if (reset) elapsedTime=0;
	float voltage=0;

	const float w=param*2*M_PI;
	voltage=sin(w*elapsedTime);
	elapsedTime+=dt;
	if (speakerdgl (voltage,dt,speaker.speakerDescriptor,speaker.v,speaker.x,speaker.i,speaker.position->crossSectionArea*speaker.position->negativeNeighbour->pressure, speaker.position->crossSectionArea*speaker.position->positiveNeighbour->pressure, speaker.airmass))
			return speaker.v;
	else
		return 0.0f;
}

float hdeltaimpuls (float dt,f1DSpeaker & speaker,int param,bool reset)
{
	if (reset)
		return 1.0f;
	return 0.0f;
}

float hcsin (float dt,f1DSpeaker & speaker,int param,bool reset)
{
	static float elapsedTime=0;
	if (reset) elapsedTime=0;
	float dummy=0;

	const float w=param*2*M_PI;
	dummy=sin(w*elapsedTime);
	elapsedTime+=dt;
	return dummy;
}

float hcsin2 (float dt,f1DSpeaker & speaker,int param,bool reset)
{
	static float elapsedTime=0;
	if (reset) elapsedTime=0;
	float dummy=0;

	const float w=param*2*M_PI;
	dummy=sin(w*elapsedTime);
	dummy*=dummy;
	elapsedTime+=dt;
	return dummy;
}

float hssin2 (float dt,f1DSpeaker & speaker,int param,bool reset)
{
	static float elapsedTime=0;
	if (reset) elapsedTime=0;
	float dummy=0;

	const float w=param*2*M_PI;
	dummy=sin(w*elapsedTime);
	dummy*=dummy;
	elapsedTime+=dt;
	if (elapsedTime>(0.5f/param)) return 0.0f;
	return dummy;
}
