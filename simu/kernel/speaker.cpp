#include "speaker.h"
//this is a speaker model.


int speakerdgl (float u,float dt,fSpeakerDescriptor const & desc,float & v,float & x,float & i,float p_left, float p_right, float airmass) // ( input to follow (e.g. voltage) ,dt, fspeakerdesc., v ,x, i amplifier current, pressureforce left, presscureforce right,airmass
{
	if( dt==0) return 1; //Null Zeitschritt = keine Änderung
	if( desc.DCResistance==0) return 0;
	if( desc.damping==0) return 0;
	if( desc.inductance==0) return 0;
	if( desc.resitanceMass==0) return 0;
	if( desc.springForce==0) return 0;
	if( desc.bl==0) return 0;
	if( desc.mass==0) return 0;

	i= (u+desc.bl*v+desc.inductance*i/dt)/(desc.DCResistance+desc.inductance/dt);
	float iind= (-desc.bl*v-desc.resitanceMass*i)/desc.resitanceMass; //inductive current
	float forceMembran=desc.bl*iind;
	float a=(forceMembran+p_left-p_right-x*desc.springForce)/(desc.mass+airmass);

	x=x+v*dt;
	v=v+a*dt;

	return 1;
}
