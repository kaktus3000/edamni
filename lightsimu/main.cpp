#include <fstream>
#include <string>
#include <list>
#include <vector>
#include <thread>
#include <memory.h>

// import C code (linker binary interface hint)
extern "C"
{
#include "kernel.h"
#include "elemFile.h"
#include "speaker.h"
}

#include "scanINI.h"

void runThread(float fFreq, SSimuSettings* pSettings, SKernelArray* pArray, SSpeaker* pSpeakers, uint* pSpeakerElems, uint nSpeakers)
{
	// create copy of speakers
	SSpeaker* pCurrSpeakers = (SSpeaker* ) calloc(nSpeakers, sizeof(SSpeaker));

	memcpy(pCurrSpeakers, pSpeakers, nSpeakers * sizeof(SSpeaker) );

	// create copy of kernel arrays
    // reserve array for microphone results
	uint nTimesteps = 1;
	for(uint uiTimeStep = 0; uiTimeStep < nTimesteps; uiTimeStep++)
	{
		float fTotalTime = (float) uiTimeStep * pSettings->m_fDeltaT;
		float fVoltage = sinf(fTotalTime * 2.0f * M_PI * fFreq);

		for(uint iSpeaker = 0; iSpeaker < nSpeakers; iSpeaker++)
		{
			SSpeaker* pSpeaker = &pCurrSpeakers[iSpeaker];
			// get pressures
			uint uiSpeakerElem = pSpeakerElems[iSpeaker];

			float fPresLeft = pArray->m_pfPressureElements[uiSpeakerElem - 1];
			float fPresRight = pArray->m_pfPressureElements[uiSpeakerElem];

			float fSpeakerVelo = simulateSpeaker(pSpeaker, pSettings, fPresRight - fPresLeft, fVoltage);

			// implant speaker velocity to field
		}

		simulate(pArray);
	}

    // calculate SPL values for mics
}

void
calculateTimeStep(SSimuSettings* pSettings, Elem* pElems, uint nElements, SSpeaker* pSpeakers, uint nSpeakers)
{
	float fTimeStep = 1e+30;

	//fTimeStep = min(fTimeStep, g_fMaxTimeStep);

	// time constraints
	// speed of sound
	fTimeStep = fmin(fTimeStep, pSettings->m_fDeltaX / sqrtf(pSettings->m_fGasConstant* pSettings->m_fTemperature));

	// acoustic damping
	float fMaxDamping = 0;
	for(uint iElem = 0; iElem < nElements; iElem++)
		fMaxDamping = fmax(fMaxDamping, pElems->m_fDamping);

	fTimeStep = fmin(fTimeStep, pSettings->m_fDensity / fMaxDamping );

	// iterate speakers
	for(uint iSpeaker = 0; iSpeaker < nSpeakers; iSpeaker++)
	{
		SSpeaker* pSpeaker = pSpeakers + iSpeaker;
		// speaker electric
		fTimeStep = fmin(fTimeStep, pSpeaker->le / pSpeaker->re);
		// mechanical damping speaker
		fTimeStep = fmin(fTimeStep, pSpeaker->mms * pSpeaker->rms);
		// mechanical spring speaker
		fTimeStep = fmin(fTimeStep, sqrtf(pSpeaker->mms * pSpeaker->cms));
	}

	pSettings->m_fDeltaT = fTimeStep;
	pSettings->m_fVelocityFactor = fTimeStep / (pSettings->m_fDensity * pSettings->m_fDeltaX);
}

int
main(int argc, char** argv)
{
	SSimuSettings simuSettings;

	// set standard atmosphere
	simuSettings.m_fDensity = 1.2041;
	simuSettings.m_fTemperature = 293.15;
	simuSettings.m_fGasConstant = 343.0;
	simuSettings.m_fReferencePressure = 0.00002;


	// read simulation input file
	std::string strInputFile(argv[1]);
	std::ifstream inFile(strInputFile, std::ios_base::in);
	ScanINI inputScanner(inFile);

	// get name of element list file
	std::string strElemFile = inputScanner.getKey("general", "element_file");

	Elem* pElems;
	uint nElems;

	std::string strBaseDir( strInputFile.substr(0, strInputFile.find_last_of("/") + 1) );

	simuSettings.m_fDeltaX = scanElemFile((strBaseDir + strElemFile).c_str(), &pElems, &nElems);

	uint* pSpeakerElems;
	uint* pMics;
	uint nSpeakers;
	uint nMics;

	getComponents(pElems, nElems, &pSpeakerElems, &nSpeakers, &pMics, &nMics);

	// create array of simulation speakersc
	SSpeaker* pSpeakers = (SSpeaker* ) calloc(nSpeakers, sizeof(SSpeaker));
	// for every speaker
	for(uint iSpeaker = 0; iSpeaker < nSpeakers; iSpeaker++)
	{
		// get speaker name
		uint uiSpeakerElem = pSpeakerElems[iSpeaker];
		std::string strSpeaker(pElems[uiSpeakerElem].m_strSpeaker);

		//find in ini file
		std::string strSpeakerFile( inputScanner.getKey("speakers", strSpeaker) );

		// open speaker ini file
		std::ifstream speakerFile(strBaseDir + strSpeakerFile, std::ios_base::in);
		ScanINI speakerScanner(speakerFile);

		SSpeaker* pSpeaker = &pSpeakers[iSpeaker];
		pSpeaker->re =  std::stof(speakerScanner.getKey("tspset", "re" ));
		pSpeaker->le =  std::stof(speakerScanner.getKey("tspset", "le" ));
		pSpeaker->rms = std::stof(speakerScanner.getKey("tspset", "rms"));
		pSpeaker->mmd = std::stof(speakerScanner.getKey("tspset", "mmd"));
		pSpeaker->cms = std::stof(speakerScanner.getKey("tspset", "cms"));
		pSpeaker->bl =  std::stof(speakerScanner.getKey("tspset", "bl" ));
		pSpeaker->sd =  std::stof(speakerScanner.getKey("tspset", "sd" ));
	}

	// determine simulation time step
	calculateTimeStep(&simuSettings, pElems, nElems, pSpeakers, nSpeakers);

	// actually run simulation

	//read frequencies to simulate
	std::string strFrequencies(inputScanner.getKey("signal", "frequencies") );

	std::list<float> lfFreqs;
	uint uiPos = 0;
	while(true)
	{
		uint uiEnd = strFrequencies.find_first_of(";", uiPos);
		std::string strFreq(strFrequencies.substr(uiPos, uiEnd));
		float fFreq = std::stof(strFreq);
		lfFreqs.push_back(fFreq);

		if(uiEnd > strFrequencies.length())
			break;

		uiPos = uiEnd+1;
	}

	SKernelArray kernelArray;
	prepareArrays(&kernelArray, &simuSettings);

	// spawn calculation threads
	std::vector<std::thread> vThreads;

	// re-init speakers
	for(uint iSpeaker = 0; iSpeaker < nSpeakers; iSpeaker++)
	{
		SSpeaker* pSpeaker = &pSpeakers[iSpeaker];
		initializeSpeaker(pSpeaker, &simuSettings);
	}

	// clear arrays
	clearArrays(&kernelArray);

	for(std::list<float>::const_iterator it = lfFreqs.begin(); it != lfFreqs.end(); it++)
	{
		float fFreq = *it;
		// start simulation
		vThreads.push_back(std::thread(runThread, fFreq, &simuSettings, &kernelArray, pSpeakers, nSpeakers) );
	}

	// Wait for all threads
	for(uint uiFreq = 0; uiFreq < lfFreqs.size(); uiFreq++)
		vThreads[uiFreq].join();

	// now proceed with calculation results

}

