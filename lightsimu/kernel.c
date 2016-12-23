#include <xmmintrin.h>
#include <stdlib.h>
#include <memory.h>
#include "common.h"
#include "kernel.h"

void
prepareArrays(SKernelArray* pArray, SSimuSettings* pSsettings)
{
	// allocate memory for pressure elements and corresponding factors

	// has to be one element longer than needed
	// shifted one tuple to the right to enable reading element -1
	pArray->m_nPressure4Tuples = (pArray->m_nElements) / 4 + 2;

	float** appfArrays[6] = {&pArray->m_pfPressureElements,
			&pArray->m_pfPressureFactorsLeft, &pArray->m_pfPressureFactorsRight,
			&pArray->m_pfPressureDifferences,
			&pArray->m_pfDampingCoefficients,
			&pArray->m_pfInfinityCoefficients,
	};

	uint iArray = 0;
	for(; iArray < 6; iArray++)
	{
		posix_memalign((void**)appfArrays[iArray], sizeof(__m128), pArray->m_nPressure4Tuples * sizeof(__m128));
		//memset(*(appfArrays[iArray]), 0, pArray->m_nPressure4Tuples * sizeof(__m128));
	}
}

void
clearArrays(SKernelArray* pArray)
{
	float* apfArrays[2] = {pArray->m_pfPressureElements, pArray->m_pfPressureDifferences};

	uint iArray = 0;
	for(; iArray < 2; iArray++)
		memset(apfArrays[iArray], 0, pArray->m_nPressure4Tuples * sizeof(__m128));
}

void
freeArrays(SKernelArray* pArray)
{
	free(pArray->m_pfPressureElements);
	free(pArray->m_pfPressureFactorsLeft);
	free(pArray->m_pfPressureFactorsRight);
	free(pArray->m_pfPressureDifferences);
	free(pArray->m_pfDampingCoefficients);
	free(pArray->m_pfInfinityCoefficients);
}

void
simulate(SKernelArray* pArray)
{
	//simulate one time step

	// calculate pressures
	uint iTuple = 1;
	for(; iTuple < pArray->m_nPressure4Tuples - 1; iTuple++)
	{
		uint uiTupleOffset = 4 * iTuple;

		//get previous pressure result
		const __m128 v4fLastPressure = _mm_load_ps(pArray->m_pfPressureElements + uiTupleOffset);

		// get previous pressure differences
		const __m128 v4fPressureDifferencesRight = _mm_load_ps (pArray->m_pfPressureDifferences + uiTupleOffset );
		const __m128 v4fPressureDifferencesLeft  = _mm_loadu_ps(pArray->m_pfPressureDifferences + uiTupleOffset - 1);

		// get constant pressure factors
		const __m128 v4fPressureFactorsRight = _mm_load_ps(pArray->m_pfPressureFactorsRight + uiTupleOffset );
		const __m128 v4fPressureFactorsLeft  = _mm_load_ps(pArray->m_pfPressureFactorsLeft  + uiTupleOffset );

		// calculate delta pressures
		const __m128 v4fDeltaRight = _mm_mul_ps(v4fPressureDifferencesRight, v4fPressureFactorsRight);
		const __m128 v4fDeltaLeft  = _mm_mul_ps(v4fPressureDifferencesLeft , v4fPressureFactorsLeft);

		__m128 v4fCurrentPressure = _mm_add_ps(_mm_add_ps(v4fLastPressure, v4fDeltaRight), v4fDeltaLeft);

		// apply damping to "infinity" elements
		const __m128 v4fInfinityCoefficients = _mm_load_ps (pArray->m_pfInfinityCoefficients + uiTupleOffset);
		v4fCurrentPressure = _mm_mul_ps(v4fCurrentPressure, v4fInfinityCoefficients);

		// integrate pressure and save
		_mm_store_ps(pArray->m_pfPressureElements + uiTupleOffset, v4fCurrentPressure);
	}

	// update pressure element link masters
	uint uiLink = 0;
	for(; uiLink < pArray->m_nLinks; uiLink++)
		pArray->m_pfPressureElements[OFFSET + pArray->m_piLinkMaster[uiLink] ] += pArray->m_pfPressureElements[OFFSET + pArray->m_piLinkSlave[uiLink] ] - pArray->m_pfLinkPressure[uiLink];

	//update presseure element link slaves
	uiLink = 0;
	for(; uiLink < pArray->m_nLinks; uiLink++)
		//update link pressure buffer
		pArray->m_pfLinkPressure[uiLink] = pArray->m_pfPressureElements[OFFSET + pArray->m_piLinkSlave[uiLink] ] = pArray->m_pfPressureElements[OFFSET + pArray->m_piLinkMaster[uiLink] ];

	// calculate pressure differences
	iTuple = 1;
	for(; iTuple < pArray->m_nPressure4Tuples - 1; iTuple++)
	{
		uint uiTupleOffset = 4 * iTuple;

		const __m128 v4fLeftPressure  = _mm_load_ps (pArray->m_pfPressureElements + uiTupleOffset);
		const __m128 v4fRightPressure = _mm_loadu_ps(pArray->m_pfPressureElements + uiTupleOffset + 1);
		const __m128 v4fLastPressureDifference = _mm_load_ps(pArray->m_pfPressureDifferences + uiTupleOffset);

		const __m128 v4fDelta = _mm_sub_ps(v4fLeftPressure, v4fRightPressure);

		__m128 v4fCurrentPressureDifference = _mm_add_ps(v4fLastPressureDifference, v4fDelta);

		// apply damping to the velocities (in the form of pressure differences)
		const __m128 v4fDampingCoefficients = _mm_load_ps (pArray->m_pfDampingCoefficients + uiTupleOffset);
		v4fCurrentPressureDifference = _mm_sub_ps(v4fCurrentPressureDifference, _mm_mul_ps( v4fCurrentPressureDifference, v4fDampingCoefficients));

		// apply damping to "infinity" elements
		const __m128 v4fInfinityCoefficients = _mm_load_ps (pArray->m_pfInfinityCoefficients + uiTupleOffset);
		v4fCurrentPressureDifference = _mm_mul_ps(v4fCurrentPressureDifference, v4fInfinityCoefficients);

		// save result
		_mm_store_ps(pArray->m_pfPressureDifferences + uiTupleOffset, v4fCurrentPressureDifference);
	}

}
