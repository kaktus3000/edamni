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
	const double fEpsU = 1e-10;
	const double fEpsF = 1e-10;
	const double fEpsV = 1e-8;
	unsigned int uiIter = 0;

	int bConverged = 0;

	// initial guess from last step
	double fCurrent = pSpeaker->m_fI;
	double fPosition = pSpeaker->m_fX;
	double fVelocity = pSpeaker->m_fV;

	double fDeltaU, fDeltaF, fDeltaV;

	const double dt= pSettings->m_fDeltaT;

	const double fDeterminant = 1.0 / ((4*pSpeaker->re*dt+8*pSpeaker->le)*pSpeaker->mms+pSpeaker->sms*pSpeaker->re*dt*dt*dt+(2*pSpeaker->re*pSpeaker->rms+2*pSpeaker->sms*pSpeaker->le+2*pSpeaker->bl*pSpeaker->bl)*dt*dt+4*pSpeaker->le*pSpeaker->rms*dt);
	// iteration loop
	for(; uiIter < nMaxIter; uiIter++)
	{
		// calculate error
		fDeltaU = (double)fVoltage - pSpeaker->bl * (fVelocity + pSpeaker->m_fV) / 2 - pSpeaker->re * (fCurrent + pSpeaker->m_fI) / 2 - pSpeaker->le * (fCurrent - pSpeaker->m_fI) / dt;
		fDeltaF = pSpeaker->bl * (fCurrent + pSpeaker->m_fI) / 2 - pSpeaker->sd * (double)fPressureDiff - pSpeaker->sms * (fPosition + pSpeaker->m_fX) / 2 - pSpeaker->rms * (fVelocity + pSpeaker->m_fV) / 2 - pSpeaker->mms * (fVelocity - pSpeaker->m_fV) / dt;
		fDeltaV = (fPosition - pSpeaker->m_fX) / dt - (fVelocity + pSpeaker->m_fV) / 2;

		// check for convergence
		if(fabs(fDeltaU) < fEpsU && fabs(fDeltaF) < fEpsF && fabs(fDeltaV) < fEpsV)
		{
			bConverged = 1;
			break;
		}

		// iterate to next guess
		fCurrent = fCurrent + fDeterminant * (8*fDeltaU*dt*pSpeaker->mms+(2*fDeltaU-2*pSpeaker->bl*fDeltaV)*pSpeaker->sms*dt*dt*dt+(4*fDeltaU*pSpeaker->rms-4*pSpeaker->bl*fDeltaF)*dt*dt);
		fPosition = fPosition + fDeterminant * -((4*fDeltaV*pSpeaker->re*dt*dt+8*fDeltaV*pSpeaker->le*dt)*pSpeaker->mms+(2*fDeltaV*pSpeaker->re*pSpeaker->rms-2*fDeltaF*pSpeaker->re+2*pSpeaker->bl*pSpeaker->bl*fDeltaV-2*pSpeaker->bl*fDeltaU)*dt*dt*dt+(4*fDeltaV*pSpeaker->le*pSpeaker->rms-4*fDeltaF*pSpeaker->le)*dt*dt);
		fVelocity = fVelocity + fDeterminant * (2*fDeltaV*pSpeaker->sms*pSpeaker->re*dt*dt*dt+(4*fDeltaF*pSpeaker->re+4*fDeltaV*pSpeaker->sms*pSpeaker->le+4*pSpeaker->bl*fDeltaU)*dt*dt+8*fDeltaF*pSpeaker->le*dt);
	}

	if(!bConverged)
		printf("speaker equations failed to converge! %e, %e, %e\n", fDeltaU, fDeltaF, fDeltaV);

	// save results
	pSpeaker->m_fV = fVelocity;
	pSpeaker->m_fX = fPosition;
	pSpeaker->m_fI = fCurrent;

	return pSpeaker->m_fV;
}
