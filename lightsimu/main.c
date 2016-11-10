#include "kernel.h"
#include "elemFile.h"

int
main(int argc, char** argv)
{
	Elem* pElems;
	uint nElems;
	scanElemFile(argv[1], &pElems, &nElems);

	uint* pSpeakers;
	uint* pMics;
	uint nSpeakers;
	uint nMics;

	getComponents(pElems, nElems, &pSpeakers, &nSpeakers, &pMics, &nMics);

}
