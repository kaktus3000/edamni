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

#ifndef simtyps_h
#define simtyps_h

//constants
//common constants
#define PI       3.14159265358979323846
#define CSOUND 343.0 //accoustic speed [m/s]
#define DENSITY  1.2041 // density of air[kg/m3]
#define TEMPERATURE 293.15 // in [K]
#define GASCONSTANT  287.0*1.4f // gasconstant of air [J/(kg K)]



// Referencepressure to calculate sound pressure in db
#define PRESSUREREFERENCE 0.00002 // This means a sound pressure of p 0.00002 equal zero db
#define MAX_ELEMENTS_FOR_INFINITE 1000
#define OPEN_ELEMENT_DAMPING 0.90
#define DEFAULT_NUM_OPEN_ELEMENTS 500
#define DEFAULT_TIME_STEPS 2000

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


struct fSpeakerDiscriptor{ //Description of a Speaker, TSP parameter
	float fillneeded;
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

typedef float (*pVelocityFunction) (float,fSpeakerDiscriptor*,float, float, float,float); 

struct f1DSpeaker{ //Fully Description of an element of the raw-file	
	int ID;
	fSpeakerDiscriptor* speakerDiscriptor;	//TSP parameter of the speaker
	f1DConnector* position;
	float airmass;
	float v;
	pVelocityFunction f;
};

struct f1DMicrophone{ //Fully Description of an element of the raw-file
private:
	unsigned int m_pos;
	float m_dt;
	std::vector<float> m_values;
public:
	int ID;	
	f1DElement* refE; //id of messured element
	f1DMicrophone(int id,unsigned int size, float dt)
	{
		ID=id;
		m_dt=dt;
		m_pos=0;
		m_values;
		for (unsigned int i=0;i<size;i++)
			m_values.push_back(0.0f);
	}
	void resize(unsigned int size){
		m_values.clear();
		for (unsigned int i=0;i<size;i++)
			m_values.push_back(0.0f);
		m_pos=0;
	}
	void resetBuffer(){
		m_pos=0;
		for (unsigned int i=0;i<m_values.size();i++)
			m_values[i]=0;
	}
	bool putValue(float value)
	{
		if (m_pos<m_values.size())
		{
			m_values[m_pos]= value;
			m_pos++;
			return true;
		}
		return false;
	}
	std::ofstream& writeToStream(std::ofstream& os)
	{
		os<<ID<<'\n';
		for (unsigned int i=0;i<m_values.size();i++)
		{
			os<<i*m_dt<<'\t'<<m_values[i]<<'\n';
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
