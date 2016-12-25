#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "common.h"
#include "elemFile.h"

void
initializeElem(SElement* elem)
{
	elem->m_fDamping = 0;
	elem->m_fInfiniteDamping = 1.0f;
	elem->m_fArea = 0;
	elem->m_bBreak = FALSE;
	elem->m_bGeometry = FALSE;

	// link syntax:
	//   -1: no link
	//   0: link to "infinity"
	//   >0: link to actual element
	elem->m_iLink = -1;

	// speaker will be inserted on the velocity link to the previous pressure element
	elem->m_strSpeaker = NULL;

	// microphone definition. measures pressure of this pressure element
	elem->m_strMic = NULL;
}

float
scanElemFile(const char* strFilename, SElement** ppElems, uint* pnElems)
{
	FILE * fp;
	char * pcLine = NULL;
	size_t len = 0;
	size_t read;

	fp = fopen(strFilename, "r");
	if (fp == NULL)
		exit(EXIT_FAILURE);

	uint nElems = 0;
	while ((read = getline(&pcLine, &len, fp)) != -1) {
		if(strncmp(pcLine, "e", 1) == 0)
			nElems++;
	}

	rewind(fp);
	// allocate elements
	SElement* aElems = (SElement*) calloc(nElems, sizeof(SElement) );

	uint iElem = 0;
	for(; iElem < nElems; iElem++)
		initializeElem(& aElems[iElem]);

	iElem = -1;
	float fDeltaX = -1.0f;

	char buf[100];

	while ((read = getline(&pcLine, &len, fp)) != -1) {
		if(strlen(pcLine) < 1)
			continue;

		switch(pcLine[0])
		{
		case 'e':
		{
			uint i;
			sscanf(pcLine, "e %d", &i);

			iElem++;
			if(i != iElem)
				printf("scanFile: ERROR element number %d not expected (%d)", i, iElem);
			break;
		}
		case 'd':
			sscanf(pcLine, "d %f", &aElems[iElem].m_fDamping);
			break;
		case 'i':
			sscanf(pcLine, "i %f", &aElems[iElem].m_fInfiniteDamping);
			break;
		case 'A':
			sscanf(pcLine, "A %f", &aElems[iElem].m_fArea);
			break;
		case 'l':
			sscanf(pcLine, "l %d", &aElems[iElem].m_iLink);
			break;
		case 'b':
			aElems[iElem].m_bBreak = TRUE;
			break;
		case 's':
			sscanf(pcLine, "s %s", buf);
			buf[strlen(buf)-1] = 0;
			aElems[iElem].m_strSpeaker = strdup(buf + 1);
			break;
		case 'm':
			sscanf(pcLine, "m %s", buf);
			buf[strlen(buf)-1] = 0;
			aElems[iElem].m_strMic = strdup(buf + 1);
			break;
		case 'g':
			aElems[iElem].m_bGeometry = TRUE;
			break;
		case 'x':
			sscanf(pcLine, "x %f", &fDeltaX);
			break;
		case '#':
			break;
		default:
			pcLine[strlen(pcLine) - 1] = 0;
			printf("scanFile: ERROR line %s not recognized\n", pcLine);
		}
	}
	fclose(fp);
	free(pcLine);

	*ppElems = aElems;
	*pnElems = nElems;

	return fDeltaX;
}

void
getComponents(const SElement* aElems, uint nElems,
		uint** ppSpeakers, uint* pnSpeakers,
		uint** ppMics, uint* pnMics)
{
	*ppSpeakers = NULL;
	*ppMics = NULL;

	*pnMics = 0;
	*pnSpeakers = 0;

	uint iElem = 0;
	for(; iElem < nElems; iElem ++)
	{
		if(aElems[iElem].m_strSpeaker )
		{
			(*pnSpeakers)++;
			*ppSpeakers = (uint*) realloc(*ppSpeakers, *pnSpeakers * sizeof(uint));
			(*ppSpeakers)[*pnSpeakers - 1] = iElem;
		}
		if(aElems[iElem].m_strMic )
		{
			(*pnMics)++;
			*ppMics = (uint*) realloc(*ppMics, *pnMics * sizeof(uint));
			(*ppMics)[*pnMics - 1] = iElem;
		}
	}
}
