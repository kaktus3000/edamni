import math
import sys

def infinitySection(fInitialCrossSection, fInfinitySpaceRatio, fSpaceLength, fTransitionLength, fStep):
	# calculate radius of sphere cap
	fRadius0 = math.sqrt(fInitialCrossSection / (4.0 * math.pi * fInfinitySpaceRatio))

	lCrossSections = []

	nSpaceSteps = int(fSpaceLength / fStep) + 1
	for i in range(1,nSpaceSteps):
		r = i*fStep
		fSpaceArea = fInfinitySpaceRatio * 4.0 * math.pi * (fRadius0 + r) ** 2
		
		lCrossSections.append(fSpaceArea)
		
	nTransitionSteps = int(fTransitionLength / fStep)
	
	fSpaceSlope = fInfinitySpaceRatio * math.pi * 8.0 * (fRadius0 + r)

	fTransParameter = 0.5 * fSpaceSlope / fTransitionLength
	
	fTransEndArea = fTransParameter * fTransitionLength ** 2 + lCrossSections[-1]
	
	for i in range(nTransitionSteps):
		x = (i+1)*fStep
		
		l = fTransitionLength - x
		
		fTransArea = fTransParameter * l * l
		
		lCrossSections.append(fTransEndArea - fTransArea)
		
	return lCrossSections

