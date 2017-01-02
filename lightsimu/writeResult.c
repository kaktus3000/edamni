#include "writeResult.h"

#include <stdlib.h>
#include <stdio.h>

void writeTable(const char* szFile, const float* pfFirstCol, float** ppfData, uint nColumns, uint nRows)
{
	FILE* fp = fopen(szFile, "w");
	if (fp == NULL)
		exit(EXIT_FAILURE);

	uint uiRow = 0;
	for(; uiRow < nRows; uiRow++)
	{
		fprintf(fp, "%f", pfFirstCol[uiRow]);

		uint uiCol = 0;
		for(; uiCol < nColumns; uiCol++)
		{
			fprintf(fp, "\t%f", ppfData[uiCol][uiRow]);
		}

		fprintf(fp, "\n");
	}
}
