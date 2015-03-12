
#include "testfunction.h"
#define _USE_MATH_DEFINES
#include <math.h>



float deltaimpuls (float dt,fSpeakerDiscriptor* desc,float v_old, float p_minus, float p_plus, float airmass)
{
	if (dt==0)
		return 1.0f;
	return 0.0f;
}

float tsin (float dt,fSpeakerDiscriptor* desc,float v_old, float p_minus, float p_plus, float airmass)
{
	float dummy=0;
	const float w=5000*2*M_PI;
	dummy=sin(w*dt);
	if ((dt*w)>=(2*M_PI))
		return 0.0f;
	return dummy;
}

float tsin2 (float dt,fSpeakerDiscriptor* desc,float v_old, float p_minus, float p_plus, float airmass)
{
	float dummy=0;
	const float w=200*2*M_PI;
	dummy=sin(w*dt)*sin(w*dt);
	if ((dt*w)>=(M_PI))
		return 0.0f;
	return dummy;
}