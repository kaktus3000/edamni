#ifndef KERNEL_KERNEL_H_
#define KERNEL_KERNEL_H_

#include "common.h"

#define OFFSET 4

typedef struct
{
	uint m_nElements;
	uint m_nPressure4Tuples;

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

void
prepareArrays(SKernelArray* pArray, SSimuSettings* pSettings);

void
clearArrays(SKernelArray* pArray);

void
freeArrays(SKernelArray* pArray);

void
simulate(SKernelArray* pArray);

#endif /* KERNEL_KERNEL_H_ */
