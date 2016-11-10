#ifndef KERNEL_KERNEL_H_
#define KERNEL_KERNEL_H_

#include "common.h"

typedef struct
{
	uint m_nElements;
	uint m_nPressure4Tuples;

	// the factor to calculate the velocity from the integrated pressure difference
	float m_fVelocityFactor;


	// pressure element list and number of elements
	float* m_pfPressureElements;
	uint m_nPressureElements;

	// factors and indices to the two linked velocity elements
	float* m_pfPressureFactorsLeft;
	float* m_pfPressureFactorsRight;

	// some elements may have a link to another element
	uint* m_piLinkMaster;
	uint* m_piLinkSlave;
	float* m_pfLinkPressure;
	uint m_nLinks;

	// pressure differences as a proxy to velocities
	float* m_pfPressureDifferences;

} SKernelArray;

typedef struct
{
	float m_fDeltaT;
	float m_fRho;
	float m_fDeltaX;
} SSimuSettings;

void prepareArrays(SKernelArray* pArray, SSimuSettings settings);
void simulate(SKernelArray* pArray, float fFrequency);

#endif /* KERNEL_KERNEL_H_ */
