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

float rms(float* pfData, uint nSamples)
{
	double fSquares = 0;

	uint iSample = 0;
	for (iSample = 0; iSample < nSamples; iSample++)
		fSquares += pfData[iSample] * pfData[iSample];

	return sqrtf(fSquares / (double)nSamples );
}

float spl(float fRMS, SSimuSettings* pSettings)
{
	return 20.0 * log10f(fRMS / pSettings->m_fReferencePressure);
}

void runThread(float fFreq,
		SSimuSettings* pSettings, SKernelArray* pArray,
		SSpeaker* pSpeakers, uint* pSpeakerElems, uint nSpeakers,
		uint* pMics, uint nMics,
		float* pSPLs)
{
	// create copy of speakers
	SSpeaker* pCurrSpeakers = (SSpeaker* ) calloc(nSpeakers, sizeof(SSpeaker));
	memcpy(pCurrSpeakers, pSpeakers, nSpeakers * sizeof(SSpeaker) );

	// create copy of kernel arrays
	SKernelArray kernelArray = *pArray;
	prepareArrays(&kernelArray, pSettings);
	clearArrays(&kernelArray);
	//copy data
	memcpy(kernelArray.m_pfPressureFactorsLeft, pArray->m_pfPressureFactorsLeft, kernelArray.m_nElements * sizeof(float));
	memcpy(kernelArray.m_pfPressureFactorsRight, pArray->m_pfPressureFactorsRight, kernelArray.m_nElements * sizeof(float));

	memcpy(kernelArray.m_piLinkMaster, pArray->m_piLinkMaster, kernelArray.m_nLinks* sizeof(uint));
	memcpy(kernelArray.m_piLinkSlave, pArray->m_piLinkSlave, kernelArray.m_nLinks * sizeof(uint));

	// calculate number of timesteps to simulate
	float fSpeed = 340.0f;
	float fFlightTime = pArray->m_nElements * pSettings->m_fDeltaX / fSpeed;
	float fSimulationDuration = pSettings->m_fLeadTime + fFlightTime + 1.0f / fFreq * pSettings->m_nSimulationPeriods;

	uint nTimesteps = fSimulationDuration / pSettings->m_fDeltaT;
	uint nLeadSteps = pSettings->m_fLeadTime / pSettings->m_fDeltaT;

    // reserve array for microphone results
	float** ppfMicMeasurements = (float**)calloc(nMics, sizeof(float*));
	for (uint uiMic = 0; uiMic < nMics; uiMic++)
		ppfMicMeasurements[uiMic] = (float*)calloc(nTimesteps, sizeof(float));

	for(uint uiTimeStep = 0; uiTimeStep < nTimesteps; uiTimeStep++)
	{
		float fTotalTime = (float) uiTimeStep * pSettings->m_fDeltaT;
		float fVoltage = 4.0f * sinf(fTotalTime * 2.0f * M_PI * fFreq);

		for(uint iSpeaker = 0; iSpeaker < nSpeakers; iSpeaker++)
		{
			SSpeaker* pSpeaker = &pCurrSpeakers[iSpeaker];
			// get pressures
			uint uiSpeakerElem = pSpeakerElems[iSpeaker];

			float fPresLeft = pArray->m_pfPressureElements[uiSpeakerElem - 1];
			float fPresRight = pArray->m_pfPressureElements[uiSpeakerElem];

			float fSpeakerVelo = simulateSpeaker(pSpeaker, pSettings, fPresRight - fPresLeft, fVoltage);

			// implant speaker velocity to field
			pArray->m_pfPressureDifferences[uiSpeakerElem] = fSpeakerVelo / pSettings->m_fVelocityFactor;
		}

		simulate(pArray);

		int iStorageStep = (int)uiTimeStep > (int)nLeadSteps;
		if( iStorageStep > 0)
			for (uint uiMic = 0; uiMic < nMics; uiMic++)
			{
				uint uiMicElem = pMics[uiMic];
				ppfMicMeasurements[uiMic][iStorageStep] = pArray->m_pfPressureElements[uiMicElem];
			}
	}

    // calculate SPL values for mics
	float* pfSumData = (float*)calloc(nTimesteps, sizeof(float));

	for (uint uiMic = 0; uiMic < nMics; uiMic++)
	{
		for (uint uiSample = 0; uiSample < nTimesteps; ++uiSample)
			pfSumData[uiSample] += ppfMicMeasurements[uiMic][uiSample];

		pSPLs[uiMic] = spl(rms(ppfMicMeasurements[uiMic], nTimesteps - nLeadSteps), pSettings);
	}
	pSPLs[nMics] = spl(rms(pfSumData, nTimesteps - nLeadSteps), pSettings);
}

void
calculateTimeStep(SSimuSettings* pSettings, SElement* pElems, uint nElements, SSpeaker* pSpeakers, uint nSpeakers)
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

	SElement* pElems;
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

	//allocate simulation data array
	SKernelArray kernelArray;
	prepareArrays(&kernelArray, &simuSettings);

	// calculate field simulation coefficients

	for(uint iElem = 1; iElem < nElems; iElem++)
	{
		SElement elem = pElems[iElem];

		// collect infinity elements
		//kernelArray.m_[iElem] = elem.m_;

		// collect damping coefficients
		//kernelArray.m_pfDamping = elem.m_fDamping;

		float fNegArea = pElems[iElem - 1].m_fArea;
		float fPosArea = elem.m_fArea;

		// calculate volume
		float fVolume = 0.5 * (fNegArea + fPosArea) * simuSettings.m_fDeltaX;

		// this factor is missing time step and velocity factor
		float fFactor = simuSettings.m_fDensity * simuSettings.m_fGasConstant * simuSettings.m_fTemperature/ fVolume;

		// implement breaks on the left side of the element
		if(elem.m_bBreak and iElem > 0)
		{
			kernelArray.m_pfPressureFactorsRight[iElem - 1] = 0;
			fNegArea = 0;
		}

		kernelArray.m_pfPressureFactorsLeft[iElem ] = fNegArea * fFactor;
		kernelArray.m_pfPressureFactorsRight[iElem ] = -fPosArea * fFactor;

		// take care of links
		/*
		if elem.m_iLink != -1:
			if elem.m_fArea != aElems[elem.m_iLink].m_fArea:
				print("lightsim: ERROR linked element areas do not match!", iElem, elem.m_iLink)

			aPressureLinks.append( (elem.m_iLink, iElem) )
		*/
	}

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
		float* pfResults = (float*)calloc(nMics + 1, sizeof(float));

		vThreads.push_back(std::thread(runThread, fFreq, &simuSettings, &kernelArray, pSpeakers, pSpeakerElems, nSpeakers, pMics, nMics, pfResults) );
	}

	// Wait for all threads
	for(uint uiFreq = 0; uiFreq < lfFreqs.size(); uiFreq++)
		vThreads[uiFreq].join();

	// now proceed with calculation results

}
