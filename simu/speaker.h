#include <math.h>
#include "common.h"

typedef struct
{
	// speaker parameters
	double re;
	double le;
	double rms;
	double mmd;
	double cms;
	double bl;
	double sd;
	// derived values
	double mms;
	double sms;

	// simulation values

	// mechanical values
	double m_fX;
	double m_fV;

	// electrical values
	double m_fI;

} SSpeaker;

void
initializeSpeaker(	SSpeaker* pSpeaker, SSimuSettings* pSettings);

float
simulateSpeaker(SSpeaker* pSpeaker, SSimuSettings* pSettings, float fPressureDiff, float fVoltage);
