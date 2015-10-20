#include "postprocessing.h"
#include <stdlib.h>
#include <math.h>
#include "fft.h"

float getMaxAmplitude(CArray data)
{
	float temp=0;
	for (unsigned int i=0; i<data.size();i++)//einschwingvorgang ignorieren
	{
		if (data[i].real()>temp)
		{
			temp=data[i].real();
		}
	}
	return temp;
}

float getAmplitude(f1DMicrophone & data,float & k1,float & k2,float & k3,int ignoresteps)
{
	if (data.getSize()<=ignoresteps) return 0.0f; //einschwingvorgang ignorieren

	int blocklength=data.getSize()-ignoresteps; //länge datenblock für die fft

	if (blocklength<2) return 0.0f; //zu wenig daten

	int offset = 0;						 // zusätzliche daten die ignorerit werden um fft blocklänge zu erreichen	 vielfaches von 2^n

	int temp=0;
	for (int i=2;i<blocklength;i*=2)
	{
		temp+=1;
	}
	int fft_blocklength;
	fft_blocklength=1<<temp;

	offset=blocklength-fft_blocklength;

	CArray c_data(fft_blocklength);

	std::complex<double> dummy;
	for (unsigned int i=0;i<c_data.size();i++)
	{
		dummy=data.getValue(i+ignoresteps+offset);//einschwingvorgang ignorieren
		c_data[i]=dummy;
	}

	fft(c_data); // do fft

	// get highest amplitude
	return 20*log10(getMaxAmplitude(c_data)/PRESSUREREFERENCE);
}

float getRMS(f1DSpeakerMonitor & data,int ignoresteps)
{
	if (data.getSize()<=ignoresteps) return 0.0f;
	if (data.getDt()<=0) return 0.0f;
	double temp=0.0f;
	for (int i=ignoresteps; i<data.getSize();i++)
	{
		temp+=data.getU(i)*data.getI(i);
	}
	temp=temp/(data.getSize()-ignoresteps);
	return float(temp);
}

float getImpedanz(f1DSpeakerMonitor & data,int ignoresteps)
{
	if (data.getSize()<=ignoresteps) return 0.0f;
	if (data.getDt()<=0) return 0.0f;
	double temp=0.0f;
	double dummy=0.0f;
	for (int i=ignoresteps; i<data.getSize();i++)
	{
		temp+=sqrt(data.getU(i)*data.getU(i));
		dummy+=sqrt(data.getI(i)*data.getI(i));
	}
	temp=temp/dummy;
	return float(temp);
}
