#ifndef COMMON_H_
#define COMMON_H_

typedef unsigned int uint;
#define FALSE 0
#define TRUE -1

typedef struct
{
	// basic constants

	// density of air [kg/m3]
	float m_fDensity;
	// temperature of air [K]
	float m_fTemperature;
	// gas constant of air [J/(kg K)]
	float m_fGasConstant;
	// gas isentropic exponent [-]
	float m_fIsentropicExponent;
	// reference pressure for 0 dB [Pa]
	float m_fReferencePressure;
	// input voltage amplitude for harmonic excitation
	float m_fVoltageAmplitude;

	// problem specific constants
	// finite spacial difference of elements
	float m_fDeltaX;

	// derived constants obeying specific constraints
	// time step for explicit integration
	float m_fDeltaT;
	// factor to calculate velocities from pressure differences
	float m_fVelocityFactor;

	// lead time for measurement (to allow for stationary state)
	float m_fLeadTime;
	// number of wave periods to average over
	float m_nSimulationPeriods;
	// signal type
	char m_szSignalType[50];

} SSimuSettings;

#endif /* COMMON_H_ */
