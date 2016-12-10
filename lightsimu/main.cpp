#include <fstream>
#include <string>

// import C code (linker binary interface hint)
extern "C"
{
#include "kernel.h"
#include "elemFile.h"
#include "speaker.h"
}

#include "scanINI.h"


int
main(int argc, char** argv)
{
	// read simulation input file
	std::string strInputFile(argv[1]);
	std::ifstream inFile(strInputFile, std::ios_base::in);
	ScanINI inputScanner(inFile);

	SSimuSettings simuSettings;

	std::string strElemFile = inputScanner.getKey("general", "element_file");

	Elem* pElems;
	uint nElems;
	scanElemFile(strElemFile.c_str(), &pElems, &nElems);

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

		// open speaker ini file
		std::string strSpeakerFile;
		std::ifstream speakerFile(strSpeakerFile, std::ios_base::in);
		ScanINI speakerScanner(speakerFile);

		SSpeaker* pSpeaker = &pSpeakers[iSpeaker];
		pSpeaker->re =  atof(speakerScanner.getKey("tspset", "re" ).c_str());
		pSpeaker->le =  atof(speakerScanner.getKey("tspset", "le" ).c_str());
		pSpeaker->rms = atof(speakerScanner.getKey("tspset", "rms").c_str());
		pSpeaker->mmd = atof(speakerScanner.getKey("tspset", "mmd").c_str());
		pSpeaker->cms = atof(speakerScanner.getKey("tspset", "cms").c_str());
		pSpeaker->bl =  atof(speakerScanner.getKey("tspset", "bl" ).c_str());
		pSpeaker->sd =  atof(speakerScanner.getKey("tspset", "sd" ).c_str());
	}

	// determine simulation time step

	// actually run simulation

	SKernelArray kernelArray;
	prepareArrays(&kernelArray, &simuSettings);

	uint nFrequencies = atoi("1");

	for(uint uiFreq = 0; uiFreq < nFrequencies; uiFreq++)
	{
		float fFreq = uiFreq;
		// clear arrays
		clearArrays(&kernelArray);
		// re-init speakers
		for(uint iSpeaker = 0; iSpeaker < nSpeakers; iSpeaker++)
		{
			SSpeaker* pSpeaker = &pSpeakers[iSpeaker];

			initializeSpeaker(pSpeaker, &simuSettings);
		}

		// start simulation

		uint nTimesteps = 1;
		for(uint uiTimeStep = 0; uiTimeStep < nTimesteps; uiTimeStep++)
		{
			float fTotalTime = (float) uiTimeStep * simuSettings.m_fDeltaT;
			float fVoltage = sinf(fTotalTime * 2.0f * M_PI * fFreq);

			for(uint iSpeaker = 0; iSpeaker < nSpeakers; iSpeaker++)
			{
				SSpeaker* pSpeaker = &pSpeakers[iSpeaker];
				simulateSpeaker(pSpeaker, &simuSettings, 0, fVoltage);
			}

			simulate(&kernelArray);
		}
	}
}

