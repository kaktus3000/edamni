#include <xmmintrin.h>
#include <stdlib.h>
#include "../common.h"
#include "kernel.h"

#define OFFSET 4

void
prepareArrays(SKernelArray* pArray, SSimuSettings settings)
{
	// the factor to calculate the velocity from the integrated pressure difference
	pArray->m_fVelocityFactor = settings.m_fDeltaT / (settings.m_fRho * settings.m_fDeltaX);


	// allocate memory for pressure elements and corresponding factors

	// has to be one element longer than needed
	// shifted one tuple to the right to enable reading element -1
	pArray->m_nPressure4Tuples = (pArray->m_nElements + OFFSET) / 4 + 1;

	float** apfArrays[4] = {&pArray->m_pfPressureElements, &pArray->m_pfPressureFactorsLeft, &pArray->m_pfPressureFactorsRight, &pArray->m_pfPressureDifferences};

	uint iArray = 0;
	for(; iArray < 4; iArray++)
		posix_memalign((void**)apfArrays[iArray], sizeof(__m128), pArray->m_nPressure4Tuples * sizeof(__m128));

}

void
simulate(SKernelArray* pArray, float fFrequency)
{
	//simulation loop
	uint bBreak = FALSE;

	while(!bBreak)
	{
		// calculate pressures
		uint iTuple = 0;
		for(; iTuple < pArray->m_nPressure4Tuples; iTuple++)
		{
			uint uiTupleOffset = 4 * iTuple + OFFSET;

			const __m128 v4fLastPressure = _mm_load_ps(pArray->m_pfPressureElements + uiTupleOffset);

			const __m128 v4fPressureDifferencesRight = _mm_load_ps (pArray->m_pfPressureDifferences + uiTupleOffset );
			const __m128 v4fPressureDifferencesLeft  = _mm_loadu_ps(pArray->m_pfPressureDifferences + uiTupleOffset - 1);

			const __m128 v4fPressureFactorsRight = _mm_load_ps(pArray->m_pfPressureFactorsRight + uiTupleOffset );
			const __m128 v4fPressureFactorsLeft  = _mm_load_ps(pArray->m_pfPressureFactorsLeft  + uiTupleOffset );

			const __m128 v4fDeltaRight = _mm_mul_ps(v4fPressureDifferencesRight, v4fPressureFactorsRight);
			const __m128 v4fDeltaLeft  = _mm_mul_ps(v4fPressureDifferencesLeft , v4fPressureFactorsLeft);

			_mm_store_ps(pArray->m_pfPressureElements + uiTupleOffset, _mm_add_ps(_mm_add_ps(v4fLastPressure, v4fDeltaRight), v4fDeltaLeft) );
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
		iTuple = 0;
		for(; iTuple < pArray->m_nPressure4Tuples; iTuple++)
		{
			uint uiTupleOffset = 4 * iTuple + OFFSET;

			const __m128 v4fLeftPressure  = _mm_load_ps (pArray->m_pfPressureElements + uiTupleOffset);
			const __m128 v4fRightPressure = _mm_loadu_ps(pArray->m_pfPressureElements + uiTupleOffset + 1);
			const __m128 v4fLastPressureDifference = _mm_load_ps(pArray->m_pfPressureDifferences + uiTupleOffset);

			const __m128 v4fDelta = _mm_sub_ps(v4fLeftPressure, v4fRightPressure);

			_mm_store_ps(pArray->m_pfPressureDifferences + uiTupleOffset, _mm_add_ps(v4fLastPressureDifference, v4fDelta));
		}
	}
}
