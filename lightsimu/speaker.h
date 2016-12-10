#include <math.h>
#include "common.h"

typedef struct
{
	// speaker parameters
	float re;
	float le;
	float rms;
	float mmd;
	float cms;
	float bl;
	float sd;
	// derived values
	float mms;
	float sms;

	// simulation values

	// mechanical values
	float m_fX;
	float m_fV;

	// electrical values
	float m_fI;

} SSpeaker;

void
initializeSpeaker(	SSpeaker* pSpeaker, SSimuSettings* pSettings);

float
simulateSpeaker(SSpeaker* pSpeaker, SSimuSettings* pSettings, float fPressureDiff, float fVoltage);
