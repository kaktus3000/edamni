#include <math.h>
#include "speaker.h"
#include "stdio.h"

void
initializeSpeaker(SSpeaker* pSpeaker, SSimuSettings* pSettings)
{
	float fRadius = sqrtf(pSpeaker->sd / M_PI);

	float m_fAirmass = (8.0/3.0) * pSettings->m_fDensity * fRadius* fRadius * fRadius;
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

// calculate speaker velocity

float
simulateSpeaker(SSpeaker* pSpeaker, SSimuSettings* pSettings, float fPressureDiff, float fVoltage)
{
	// convergence criteria for newton-raphson
	const unsigned int nMaxIter = 5;
	const double fEpsU = 1e-8;
	const double fEpsF = 1e-8;
	unsigned int uiIter = 0;

	int bConverged = 0;

	// initial guess from last step
	double fCurrent = pSpeaker->m_fI;
	double fPosition = pSpeaker->m_fX;

	double fDeltaU;
	double fDeltaF;

	const double dt= pSettings->m_fDeltaT;

	const double fDeterminant = 1.0/((pSpeaker->re*dt+pSpeaker->le)*pSpeaker->mms+pSpeaker->sms*pSpeaker->re*dt*dt*dt+(pSpeaker->re*pSpeaker->rms+pSpeaker->sms*pSpeaker->le+pSpeaker->bl*pSpeaker->bl)*dt*dt+pSpeaker->le*pSpeaker->rms*dt);

	// iteration loop
	for(; uiIter < nMaxIter; uiIter++)
	{
		// calculate error
		fDeltaU = (double)fVoltage - pSpeaker->bl * (fPosition - pSpeaker->m_fX) / dt - pSpeaker->re * fCurrent - pSpeaker->le * (fCurrent - pSpeaker->m_fI) / dt;
		fDeltaF = pSpeaker->bl * fCurrent - pSpeaker->sd * (double)fPressureDiff - pSpeaker->sms * fPosition - pSpeaker->rms * (fPosition - pSpeaker->m_fX) / dt - pSpeaker->mms * ((fPosition - pSpeaker->m_fX) / dt - pSpeaker->m_fV) / dt;

		// check for convergence
		if(fabs(fDeltaU) < fEpsU && fabs(fDeltaF) < fEpsF)
		{
			bConverged = 1;
			break;
		}

		// iterate to next guess
		fCurrent = fCurrent + fDeterminant * (fDeltaU*dt*pSpeaker->mms+fDeltaU*pSpeaker->sms*dt*dt*dt+(fDeltaU*pSpeaker->rms-pSpeaker->bl*fDeltaF)*dt*dt);
		fPosition = fPosition + fDeterminant * ((fDeltaF*pSpeaker->re+pSpeaker->bl*fDeltaU)*dt*dt*dt+fDeltaF*pSpeaker->le*dt*dt);
	}

	if(!bConverged)
		printf("speaker equations failed to converge! %e, %e\n", fDeltaU, fDeltaF);

	// save results
	pSpeaker->m_fV = (fPosition - pSpeaker->m_fX) / pSettings->m_fDeltaT;
	pSpeaker->m_fX = fPosition;
	pSpeaker->m_fI = fCurrent;

	return pSpeaker->m_fV;
}
