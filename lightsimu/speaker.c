#include <math.h>
#include "speaker.h"

void
initializeSpeaker(	SSpeaker* pSpeaker, SSimuSettings* pSettings)
{
	float fRadius = sqrtf(pSpeaker->sd / M_PI);

	float m_fAirmass = (8.0/3.0) * pSettings->m_fRho * fRadius* fRadius * fRadius;
	float m_fStiffness = 1.0 / pSpeaker->cms;

	pSpeaker->mms = pSpeaker->mmd + m_fAirmass;
	pSpeaker->sms = m_fStiffness;

	pSpeaker->m_fX = 0;
	pSpeaker->m_fV = 0;
	pSpeaker->m_fI = 0;

	// element cross section is given for right side (where the speaker is implemented)
	//aPressureFactorsPos[m_iElemID]     *= m_pSpeaker->sd / aElems[m_iElemID].m_fArea
	//aPressureFactorsNeg[m_iElemID + 1] *= m_pSpeaker->sd / aElems[m_iElemID].m_fArea
}

float
simulateSpeaker(SSpeaker* pSpeaker, SSimuSettings* pSettings, float fPressureDiff, float fVoltage)
{
	// calculate current
	float fCurrentSlope = (fVoltage - pSpeaker->bl * pSpeaker->m_fV - pSpeaker->re * pSpeaker->m_fI)/pSpeaker->le;
	pSpeaker->m_fI = pSpeaker->m_fI + fCurrentSlope * pSettings->m_fDeltaT;

	float fForceMembrane = pSpeaker->bl * pSpeaker->m_fI;

	// calculate speaker acceleration
	float fAcceleration = (fForceMembrane - fPressureDiff * pSpeaker->sd - pSpeaker->m_fX * pSpeaker->sms - pSpeaker->rms * pSpeaker->m_fV)/(pSpeaker->mms);

	// calculate speaker velocity
	pSpeaker->m_fV = pSpeaker->m_fV + fAcceleration * pSettings->m_fDeltaT;

	// calculate speaker position
	pSpeaker->m_fX = pSpeaker->m_fX + pSpeaker->m_fV * pSettings->m_fDeltaT;

	return pSpeaker->m_fV;
}
