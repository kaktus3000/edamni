#include <fstream>
#include <string>
#include <list>
#include <vector>
#include <thread>
#include <iostream>
#include <memory.h>

// import C code (linker binary interface hint)
extern "C"
{
#include "kernel.h"
#include "elemFile.h"
#include "speaker.h"
#include "writeResult.h"
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
		float* pfSPLs, float* pfImpedance, float* pfExcursion)
{
	// create copy of speakers
	SSpeaker* pCurrSpeakers = (SSpeaker* ) calloc(nSpeakers, sizeof(SSpeaker));
	memcpy(pCurrSpeakers, pSpeakers, nSpeakers * sizeof(SSpeaker) );

	// create copy of kernel arrays
	SKernelArray kernelArray = *pArray;
	prepareArrays(&kernelArray, pSettings);
	//copy data

	// continuum coefficients
	memcpy(kernelArray.m_pfPressureFactorsLeft, pArray->m_pfPressureFactorsLeft, kernelArray.m_nPressure4Tuples * 4 * sizeof(float));
	memcpy(kernelArray.m_pfPressureFactorsRight, pArray->m_pfPressureFactorsRight, kernelArray.m_nPressure4Tuples * 4 * sizeof(float));

	// damping coefficients
	memcpy(kernelArray.m_pfDampingCoefficients, pArray->m_pfDampingCoefficients, kernelArray.m_nPressure4Tuples * 4 * sizeof(float));

	// infinity damping coefficients
	memcpy(kernelArray.m_pfInfinityCoefficients, pArray->m_pfInfinityCoefficients, kernelArray.m_nPressure4Tuples * 4 * sizeof(float));

	// links
	memcpy(kernelArray.m_piLinkMaster, pArray->m_piLinkMaster, kernelArray.m_nLinks * sizeof(uint));
	memcpy(kernelArray.m_piLinkSlave, pArray->m_piLinkSlave, kernelArray.m_nLinks * sizeof(uint));

	clearArrays(&kernelArray);

	float fMaxExcursion = 0;

	// calculate number of timesteps to simulate
	float fSpeed = 340.0f;
	float fFlightTime = kernelArray.m_nElements * pSettings->m_fDeltaX / fSpeed;
	float fSimulationDuration = pSettings->m_fLeadTime + fFlightTime + 1.0f / fFreq * pSettings->m_nSimulationPeriods;

	uint nTimesteps = fSimulationDuration / pSettings->m_fDeltaT;
	uint nLeadSteps = pSettings->m_fLeadTime / pSettings->m_fDeltaT;

    // reserve array for microphone results
	float** ppfMicMeasurements = (float**)calloc(nMics, sizeof(float*));
	for (uint uiMic = 0; uiMic < nMics; uiMic++)
		ppfMicMeasurements[uiMic] = (float*)calloc(nTimesteps, sizeof(float));

	float* pfVoltage = (float*)calloc(nTimesteps, sizeof(float));
	float* pfCurrent = (float*)calloc(nTimesteps, sizeof(float));

	for(uint uiTimeStep = 0; uiTimeStep < nTimesteps; uiTimeStep++)
	{
		float fTotalTime = (float) uiTimeStep * pSettings->m_fDeltaT;
		float fVoltage = 4.0f * sinf(fTotalTime * 2.0f * M_PI * fFreq);

		for(uint iSpeaker = 0; iSpeaker < nSpeakers; iSpeaker++)
		{
			SSpeaker* pSpeaker = &pCurrSpeakers[iSpeaker];
			// get pressures
			uint uiSpeakerElem = pSpeakerElems[iSpeaker];

			// speaker is implemented on the right side of the speaker element
			float fPresLeft = kernelArray.m_pfPressureElements[OFFSET + uiSpeakerElem];
			float fPresRight = kernelArray.m_pfPressureElements[OFFSET + uiSpeakerElem + 1];

			float fSpeakerVelo = simulateSpeaker(pSpeaker, pSettings, fPresRight - fPresLeft, fVoltage);
			//std::cout << "speaker velocity " << fSpeakerVelo << "\n";

			// implant speaker velocity to field
			kernelArray.m_pfPressureDifferences[OFFSET + uiSpeakerElem] = fSpeakerVelo / pSettings->m_fVelocityFactor;
		}

		simulate(&kernelArray);
		
		/*
		if((uiTimeStep % 20)==0)
		{
			for(uint uiElem = OFFSET; uiElem < kernelArray.m_nElements + OFFSET; uiElem++)
				std::cout << kernelArray.m_pfPressureElements[uiElem] << "\t";
			std::cout << "\n";
			//for(uint uiElem = OFFSET; uiElem < kernelArray.m_nElements + OFFSET; uiElem++)
			//	std::cout << kernelArray.m_pfPressureDifferences[uiElem] << "\t";
			//std::cout << "\n";
		}

		if(uiTimeStep > 2)
			exit(0);

		*/

		int iStorageStep = (int)uiTimeStep - (int)nLeadSteps;
		if( iStorageStep > 0)
			for (uint uiMic = 0; uiMic < nMics; uiMic++)
			{
				uint uiMicElem = pMics[uiMic];
				ppfMicMeasurements[uiMic][iStorageStep] = kernelArray.m_pfPressureElements[OFFSET + uiMicElem];

				pfVoltage[iStorageStep] = fVoltage;
				pfCurrent[iStorageStep] = pCurrSpeakers[0].m_fI;

				fMaxExcursion = fmaxf(fMaxExcursion, fabsf(pCurrSpeakers[0].m_fX) );
			}
	}
	free(pCurrSpeakers);
	freeArrays(&kernelArray);

    // calculate SPL values for mics
	float* pfSumData = (float*)calloc(nTimesteps, sizeof(float));

	for (uint uiMic = 0; uiMic < nMics; uiMic++)
	{
		for (uint uiSample = 0; uiSample < nTimesteps; ++uiSample)
		{
			pfSumData[uiSample] += ppfMicMeasurements[uiMic][uiSample];
			//std::cout << pfSumData[uiSample] << "\t";
		}

		pfSPLs[uiMic] = spl(rms(ppfMicMeasurements[uiMic], nTimesteps - nLeadSteps), pSettings);
	}
	pfSPLs[nMics] = spl(rms(pfSumData, nTimesteps - nLeadSteps), pSettings);

	for (uint uiMic = 0; uiMic < nMics; uiMic++)
		free(ppfMicMeasurements[uiMic]);
	free(ppfMicMeasurements);
	free(pfSumData);

	*pfImpedance = rms(pfVoltage, nTimesteps - nLeadSteps) / rms(pfCurrent, nTimesteps - nLeadSteps);
	*pfImpedance = fMaxExcursion;

	free(pfVoltage);
	free(pfCurrent);

	std::cout << ".";
	std::cout.flush();
}

void
calculateTimeStep(SSimuSettings* pSettings, SElement* pElems, uint nElements, SSpeaker* pSpeakers, uint nSpeakers)
{
	float fTimeStep = pSettings->m_fDeltaT;

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

	simuSettings.m_fLeadTime = std::stof(inputScanner.getKey("signal", "lead_time"));
	simuSettings.m_nSimulationPeriods = std::stoi(inputScanner.getKey("signal", "signal_periods"));

	// get name of element list file
	std::string strElemFile = inputScanner.getKey("general", "element_file");
	simuSettings.m_fDeltaT = std::stof(inputScanner.getKey("signal", "max_timestep"));

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

		initializeSpeaker(pSpeaker, &simuSettings);
	}
	// determine simulation time step
	calculateTimeStep(&simuSettings, pElems, nElems, pSpeakers, nSpeakers);

	//allocate simulation data array
	SKernelArray kernelArray;
	kernelArray.m_nElements = nElems;
	kernelArray.m_nLinks = 0;
	prepareArrays(&kernelArray, &simuSettings);

	// calculate field simulation coefficients

	for(uint iElem = 1; iElem < nElems; iElem++)
	{
		SElement elem = pElems[iElem];

		// collect infinity elements
		kernelArray.m_pfInfinityCoefficients[OFFSET + iElem] = elem.m_fInfiniteDamping;

		// collect damping coefficients
		kernelArray.m_pfDampingCoefficients[OFFSET + iElem] = elem.m_fDamping * simuSettings.m_fDeltaX * simuSettings.m_fVelocityFactor;

		float fNegArea = pElems[iElem - 1].m_fArea;
		float fPosArea = elem.m_fArea;

		// calculate volume
		float fVolume = 0.5 * (fNegArea + fPosArea) * simuSettings.m_fDeltaX;

		// this factor is missing
		float fFactor = simuSettings.m_fDensity * simuSettings.m_fGasConstant * simuSettings.m_fTemperature * simuSettings.m_fVelocityFactor * simuSettings.m_fDeltaT / fVolume;

		// implement breaks on the left side of the element
		if(elem.m_bBreak and iElem > 0)
		{
			kernelArray.m_pfPressureFactorsRight[OFFSET + iElem - 1] = 0;
			fNegArea = 0;
		}

		kernelArray.m_pfPressureFactorsLeft[OFFSET + iElem ] = fNegArea * fFactor;
		kernelArray.m_pfPressureFactorsRight[OFFSET + iElem ] = -fPosArea * fFactor;

		//std::cout << "\t" << fNegArea * fFactor;

		// take care of links
		/*
		if elem.m_iLink != -1:
			if elem.m_fArea != aElems[elem.m_iLink].m_fArea:
				print("lightsim: ERROR linked element areas do not match!", iElem, elem.m_iLink)

			aPressureLinks.append( (elem.m_iLink, iElem) )
		*/
	}

	// implant speakers
	for(uint iSpeaker = 0; iSpeaker < nSpeakers; iSpeaker++)
	{
		// get speaker name
		uint uiSpeakerElem = pSpeakerElems[iSpeaker];
		SSpeaker* pSpeaker = &pSpeakers[iSpeaker];

		//adapt cross sections on the right side of the speaker element
		kernelArray.m_pfPressureFactorsRight[OFFSET + uiSpeakerElem ] *= pSpeaker->sd / pElems[uiSpeakerElem].m_fArea;
		kernelArray.m_pfPressureFactorsLeft[OFFSET + uiSpeakerElem + 1] *= pSpeaker->sd / pElems[uiSpeakerElem].m_fArea;
	}


	std::cout << "\n";

	//read frequencies to simulate
	std::string strFrequencies(inputScanner.getKey("signal", "frequencies") );

	std::vector<float> vfFreqs;
	uint uiPos = 0;
	while(true)
	{
		uint uiEnd = strFrequencies.find_first_of(";", uiPos);
		std::string strFreq(strFrequencies.substr(uiPos, uiEnd));
		if(!strFreq.length())
			break;
		float fFreq = std::stof(strFreq);
		vfFreqs.push_back(fFreq);

		if(uiEnd > strFrequencies.length())
			break;

		uiPos = uiEnd+1;
	}

	const uint nFreqs = vfFreqs.size();
	float* pfFreqs = (float*) calloc(nFreqs, sizeof(float));

	for(uint uiFreq = 0; uiFreq < nFreqs; uiFreq ++)
		pfFreqs[uiFreq] = vfFreqs[uiFreq];

	float** ppfThreadResults = (float**)calloc(nMics + 1, sizeof(float*));
	for(uint uiMic = 0; uiMic < nMics + 1; uiMic++)
		ppfThreadResults[uiMic] = (float*)calloc(nFreqs, sizeof(float));

	float* pfImpedances = (float*)calloc(vfFreqs.size(), sizeof(float));
	float* pfExcursions = (float*)calloc(vfFreqs.size(), sizeof(float));

	// spawn calculation threads
	std::vector<std::thread> vThreads;
	std::vector<float*> vpfResults;

	for(uint uiFreq = 0; uiFreq < nFreqs; uiFreq++)
	{
		float fFreq = pfFreqs[uiFreq];
		// start simulation
		float* pfResults = (float*)calloc(nMics + 1, sizeof(float));
		vpfResults.push_back(pfResults);

#ifdef DEBUGBUILD
		runThread( fFreq, &simuSettings, &kernelArray, pSpeakers, pSpeakerElems, nSpeakers, pMics, nMics, pfResults, &(pfImpedances[uiFreq]), &(pfExcursions[uiFreq]));
#else
		vThreads.push_back(std::thread(runThread, fFreq, &simuSettings, &kernelArray, pSpeakers, pSpeakerElems, nSpeakers, pMics, nMics, pfResults, &(pfImpedances[uiFreq]), &(pfExcursions[uiFreq]) ) );
#endif
	}

	// Wait for all threads
	for(uint uiThread = 0; uiThread < vThreads.size(); uiThread++)
		vThreads[uiThread].join();

	for(uint uiFreq = 0; uiFreq < nFreqs; uiFreq++)
	{
		float* pfResults = vpfResults[uiFreq];
		for(uint uiMic = 0; uiMic < nMics + 1; uiMic++)
			ppfThreadResults[uiMic][uiFreq] = pfResults[uiMic];

		free(pfResults);
	}

	std::string strOutFile(inputScanner.getKey("general", "output_file"));
	std::cout << "+\n" << "writing output to " << strOutFile << "\n";

	// write XML output
	std::ofstream hXML(strBaseDir + strOutFile);

	hXML << "<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<simu_output>\n";

	for (uint uiMic = 0; uiMic < nMics; uiMic++)
	{
		uint uiMicElem = pMics[uiMic];
		std::string strMic(pElems[uiMicElem].m_strMic);
		std::string strMicFile(std::string("spl_") + strMic + std::string(".dat"));

		std::cout << "writing " << strMicFile << "\n";
		writeTable((strBaseDir + strMicFile).c_str(), pfFreqs, &(ppfThreadResults[uiMic]), 1, nFreqs);

		hXML << "\t<mic_spl file=\"" << strMicFile << "\" id=\"" << strMic << "\"/>\n";
	}

	//write sum mic
	{
		std::string strMic("spl_sum");
		std::string strMicFile(std::string("spl_") + strMic + std::string(".dat"));

		std::cout << "writing " << strMicFile << "\n";
		writeTable((strBaseDir + strMicFile).c_str(), pfFreqs, &(ppfThreadResults[nMics]), 1, nFreqs);

		hXML << "\t<mic_spl file=\"" << strMicFile << "\" id=\"" << strMic << "\"/>\n";
	}

	for(uint iSpeaker = 0; iSpeaker < nSpeakers; iSpeaker++)
	{
		// get speaker name
		uint uiSpeakerElem = pSpeakerElems[iSpeaker];
		std::string strSpeaker(pElems[uiSpeakerElem].m_strSpeaker);
		std::string strSpeakerFile(std::string("imp_") + strSpeaker + std::string(".dat"));

		std::cout << "writing " << strSpeakerFile << "\n";
		writeTable((strBaseDir + strSpeakerFile).c_str(), pfFreqs, &pfImpedances, 1, nFreqs);

		std::string strSpeakerExcursionFile(std::string("exc_") + strSpeaker + std::string(".dat"));
		writeTable((strBaseDir + strSpeakerExcursionFile).c_str(), pfFreqs, &pfExcursions, 1, nFreqs);

		hXML << "\t<speaker_impedance file=\"" << strSpeakerFile << "\" id=\"" << strSpeaker << "\"/>\n";
	}
	hXML << "</simu_output>\n";

	hXML.close();

	// free buffers
	free(pSpeakers);
	free(pfFreqs);

	free(pfImpedances);
	free(pfExcursions);

	for(uint uiMic = 0; uiMic < nMics + 1; uiMic++)
		free(ppfThreadResults[uiMic]);
	free(ppfThreadResults);

	free(pSpeakerElems);
	free(pMics);

	for(uint iElem = 1; iElem < nElems; iElem++)
	{
		free(pElems[iElem].m_strMic);
		free(pElems[iElem].m_strSpeaker);
	}
	free(pElems);

	freeArrays(&kernelArray);
}

