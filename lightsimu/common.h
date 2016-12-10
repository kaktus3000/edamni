#ifndef COMMON_H_
#define COMMON_H_

typedef unsigned int uint;
#define FALSE 0
#define TRUE -1

#define M_PI 3.141592654


typedef struct
{
	float m_fDeltaT;
	float m_fRho;
	float m_fDeltaX;
} SSimuSettings;

#endif /* COMMON_H_ */
