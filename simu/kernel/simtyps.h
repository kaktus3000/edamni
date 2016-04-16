//Leapfrog Speakersimulation Project
//Headerfile created by Hendrik Levering
//� Hendrik Levering Februar 2015
//� Hendrik Levering Februar 2015, all rights reserved


//This headerfile includes all the datatypes  and constants used by this simulation project


//To do:
/****************************

-change data types for 2d calculation
-include data types for 3d /2drad simulation

-include dataformat for a speaker descriptor tsp parameter etc...

-include double types if needed
*************************/
#include <vector>
#include <ostream>      // std::flush
#include <fstream> 

#include <iostream>

#ifndef simtyps_h
#define simtyps_h

//constants
//common constants
#define PI       3.14159265358979323846
#define CSOUND 343.0 //accoustic speed [m/s]
#define DENSITY  1.2041 // density of air[kg/m3]
#define TEMPERATURE 293.15 // in [K]
#define GASCONSTANT  287.0*1.4f // gasconstant of air [J/(kg K)]

#define STARTFREQUENCY 35.0f
#define ENDFREQUENCY 700.0f
#define TENTHSQRT2 1.07177f
#define STEPSTOIGNORE 7000


// Referencepressure to calculate sound pressure in db
#define PRESSUREREFERENCE 2e-5f // This means a sound pressure of p 0.00002 equal zero db
#define MAX_ELEMENTS_FOR_INFINITE 1000
#define OPEN_ELEMENT_DAMPING 0.98f
#define DEFAULT_NUM_OPEN_ELEMENTS 50
#define DEFAULT_TIME_STEPS 10000

#define VOLTAGE_DEFAULT 4.0f

// the designation of the datatypes is of the following form
// [precision][dimensions][functionname]

// precision
//		"f"  calculation with float precision 
//		"d"  calculation with double precision
//
// dimensions
//		"1D"
//		"2D"
//		"2DRad"  //2 dimensional radialsymmetric calculation in cylindric coordinates
//		"3D"

//
//common types

// Datatypes to read speaker raw-files:

//const char* const cSpeakerFileEnding ="spk"; 


struct fSpeakerDescriptor{ //Description of a Speaker, TSP parameter
	float inductance;
	float bl;
	float DCResistance;
	float sd;
	float resitanceMass;
	float springForce;
	float mass;
};


// Datatypes to read element raw-files:
/*
const char* const c1DRawFileEnding ="txt"; 

enum e1DElementType {element,speaker,microphone}; 
const char* const c1DelementTypeDescriptor ="esm"; //char which describes elementtype in txt-file ;c1DelementTypeDescriptor[e1DElementType]
enum e1DNeighbourType {minus,plus};
const char* const c1DNeighbourTypeDescriptor = "-+"; //same for the negative and positive neighbours ;c1DNeighbourTypeDescriptor[c1DNeighbourTypeDescriptor]

*/
//1D calculation data types
struct f1DConnector;
typedef f1DConnector* pf1DConnector;



struct f1DElement{ //Fully Description of an element of the raw-file
	int ID;	
	float pressure;
	float damping;
	float pFactor;
	std::vector<int> negativeDirections;
	std::vector<int> positiveDirections;
	std::vector<pf1DConnector> negativeNeighbours; //pointer to a f1DElement/f1DSpeaker/f1DMicrophone, depending on the typ of enum
	std::vector<pf1DConnector> positiveNeighbours;
};

struct f1DConnector{ //Fully Description of an element of the raw-file
	int ID;
	f1DElement* negativeNeighbour;
	f1DElement* positiveNeighbour;
	float velocity;
	float vfactor;
	float crossSectionArea;
	float damping;
};



struct f1DSpeakerMonitor{ //Fully Description of an element of the raw-file
private:
	unsigned int m_pos;
	float m_dt;
	std::vector<float> m_u;
	std::vector<float> m_i;
	std::vector<float> m_v;
	std::vector<float> m_x;
public:
	int ID;
	f1DSpeakerMonitor()
	{
		ID=0;
		m_dt=0;
		m_pos=0;
		m_u.clear();
		m_i.clear();
		m_v.clear();
		m_x.clear();

	}
	void initialize(int id, unsigned int size, float dt)
	{
		m_dt=dt;
		ID=id;
		m_u.clear();
		m_v.clear();
		m_x.clear();
		m_i.clear();
		for (unsigned int i=0;i<size;i++)
		{
			m_u.push_back(0.0f);
			m_v.push_back(0.0f);
			m_x.push_back(0.0f);
			m_i.push_back(0.0f);
		}
		m_pos=0;

	}
	void resize(unsigned int size){
		m_u.clear();
		m_v.clear();
		m_x.clear();
		m_i.clear();
		for (unsigned int i=0;i<size;i++)
		{
			m_u.push_back(0.0f);
			m_v.push_back(0.0f);
			m_x.push_back(0.0f);
			m_i.push_back(0.0f);
		}
		m_pos=0;
	}
	void resetBuffer(){
		m_pos=0;
		for (unsigned int i=0;i<m_u.size();i++)
		{
			m_u[i]=0;
			m_i[i]=0;
			m_v[i]=0;
			m_x[i]=0;
		}
	}
	void putValue(float u,float i, float v, float x)
	{
		if (m_pos<m_u.size())
		{
			m_u[m_pos]= u;
			m_i[m_pos]= i;
			m_x[m_pos]= x;
			m_v[m_pos]= v;
			m_pos++;
		}
	}
	float getU(unsigned int index)
	{
		if (index<m_u.size())
		{
			return m_u[index];
		}
		return 0.0f;
	}
	float getI(unsigned int index)
	{
		if (index<m_i.size())
		{
			return m_i[index];
		}
		return 0.0f;
	}
	float getV(unsigned int index)
	{
		if (index<m_v.size())
		{
			return m_v[index];
		}
		return 0.0f;
	}
	float getX(unsigned int index)
	{
		if (index<m_x.size())
		{
			return m_x[index];
		}
		return 0.0f;
	}
	float getDt()
	{
		return m_dt;
	}
	int getSize()
	{
		return m_u.size();
	}
	std::ofstream& writeToStream(std::ofstream& os)
	{
		//os<<ID<<'\n';
		for (unsigned int i=0;i<m_u.size();i++)
		{
			os<<i*m_dt<<'\t'<<m_u[i]<<'\t'<<m_i[i]<<'\t'<<m_v[i]<<'\t'<<m_x[i]<<'\n';
		}
		return os;
	}
};

struct f1DSpeaker;
typedef float (*pVelocityFunction) (float ,f1DSpeaker & ,float ,bool ); // ( (dt, timestepsize, speaker, param for giving a value to the function eg frequence, reset (function will be reseted if true)

struct f1DSpeaker{ //Fully Description of an element of the raw-file	
	int ID;
	fSpeakerDescriptor speakerDescriptor;	//TSP parameter of the speaker
	f1DConnector* position;
	f1DConnector* position2;
	float airmass;
	float v;
	float x;
	float i;
	pVelocityFunction f;
	f1DSpeakerMonitor monitor;
	f1DSpeaker()
	{
		airmass=0.0f;
		x=0.0f;
		v=0.0f;
		i=0.0f;
		f=0;
		ID=0;
		position=0;
		position2=0;

	}
	void reset(pVelocityFunction ptr)
	{
		f=ptr;
		x=0.0f;
		v=0.0f;
		i=0.0f;
		monitor.resetBuffer();
	}
	void storeStatus(float u)
	{
		monitor.putValue(u,i,v,x);
	}
};

struct f1DMicrophone{ //Fully Description of an element of the raw-file
private:
	unsigned int m_pos;
	float m_dt;
	std::vector<float> m_values;
	std::vector<float> m_values2;
public:
	std::string strLabel;
	f1DElement* refE; //id of messured element
	f1DMicrophone(unsigned int size, float dt, std::string label)
	{
		m_dt=dt;
		strLabel = label;

		m_pos=0;
		m_values.clear();
		m_values2.clear();
		refE=0;
		for (unsigned int i=0;i<size;i++)
		{
			m_values.push_back(0.0f);
			m_values2.push_back(0.0f);
		}
	}
	void resize(unsigned int size){
		m_values.clear();
		m_values2.clear();
		for (unsigned int i=0;i<size;i++)
			m_values.push_back(0.0f);
			m_values2.push_back(0.0f);
		m_pos=0;
	}
	void resetBuffer(){
		m_pos=0;
		for (unsigned int i=0;i<m_values.size();i++)
		{
			m_values[i]=0;
			m_values2[i]=0;
		}
	}
	void putValue(float value,float value2 =0)
	{
		if (m_pos<m_values.size())
		{
			m_values[m_pos]= value;
			m_values2[m_pos]= value;
			m_pos++;
		}
	}
	float getValue(unsigned int index)
	{
		if (index<m_values.size())
		{
			return m_values[index];
		}
		return 0.0f;
	}
	float get()
	{
		return m_values[m_pos];
	}
	int getPos()
	{
		return m_pos;
	}
	float getValue2(unsigned int index)
	{
		if (index<m_values2.size())
		{
			return m_values2[index];
		}
		return 0.0f;
	}
	float getDt()
	{
		return m_dt;
	}
	int getSize()
	{
		return m_values.size();
	}
	std::ofstream& writeToStream(std::ofstream& os)
	{
		//os<<ID<<'\n';
		for (unsigned int i=0;i<m_values.size();i++)
		{
			os<<i*m_dt<<'\t'<<m_values[i]<<'\n';//<<m_values2[i]<<'\n';
		}
		return os;
	}
};

struct frequencyOutput{
private:
	std::vector<float> m_frequencies;
	std::vector<float> m_values;
public:
	frequencyOutput()
	{
		 m_frequencies.clear();
		 m_values.clear();
	}
	void storeData(float frequency, float value)
	{
		m_frequencies.push_back(frequency);
		m_values.push_back(value);
	}
	std::ofstream& writeToStream(std::ofstream& os)
	{
		//os<<ID<<'\n';
		for (unsigned int i=0;i<m_frequencies.size();i++)
		{
			os<<m_frequencies[i]<<'\t'<<m_values[i]<<'\n';
		}
		return os;
	}
};



struct f1DOpenElement{
	int ID;
	f1DConnector *connector;
	f1DElement element; //pointer to element where the open end element beginns;
	int direction; //+1 when connected as a positive neighbour, -1 when connected as a negative neighbour;
	std::vector<float> pField;
	std::vector<float> vField;
	std::vector<float> aField;
	std::vector<float> pFactorField;
	std::vector<float> vFactorField;
};


struct f1DCalculationDescriptor {
	float dt;
	float gasconstant;
	float density;
	float temperature;
	float OpenElementsDamping;
	unsigned int numberTimesteps;
	float OpenEndLength;
	int OpenEndElements;
};



typedef f1DMicrophone* pf1DMicrophone;
typedef f1DSpeaker* pf1DSpeaker;
typedef f1DElement* pf1DElement;
typedef f1DOpenElement* pf1DOpenElement;

struct f1DCalculationContainer{ //contains all elements and caculationinfo
	float dx;	
	f1DCalculationDescriptor* info;
	std::vector<f1DElement> elements;
	std::vector<f1DMicrophone> microphones;
	std::vector<f1DSpeaker> speakers;
	std::vector<f1DConnector> connectors;
	std::vector<f1DOpenElement> openElements;
};





#endif //simtyps_h
