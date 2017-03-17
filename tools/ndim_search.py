import math
import numpy

def toCoords(aBounds, aiCurrSample, aiResolution):
	afSample = []
	for iDim in range(len(aBounds)):
		(fMin, fMax) = aBounds[iDim]
		fRange = fMax - fMin
		afSample.append(fMin + fRange * aiCurrSample[iDim] / aiResolution[iDim])
		
	return afSample

def sample(func, aBounds, aiResolution, aiCurrSample, aBest, dCache):
	tSample = tuple(aiCurrSample)
	if tSample in dCache.keys():
		# we already samples this point, skip
		return

	# calculate coordinates in problem space
	afSample = toCoords(aBounds, aiCurrSample, aiResolution)

	# evaluate and cache result	
	fCurrResult = func(afSample)
	dCache[tSample] = fCurrResult
	
	# put result into hall of fame if good
	for iBest in range(len(aBest)):
		(fResult, aiSample) = aBest[iBest]
		if fCurrResult < fResult:
			for iPos in reversed(range(iBest,len(aBest)-1)):
				aBest[iPos+1] = aBest[iPos]
			aBest[iBest] = (fCurrResult, list(aiCurrSample))
			break

def optimize_base(func, aBounds, aiResolution, aiBase, aiStep, aBest, dCache):
	# wiggle each dimension up and down
	for iDim in range(len(aBounds)):
		aiSample = list(aiBase)
		iBase = aiSample[iDim]
		# wiggle up and sample
		aiSample[iDim] = min(iBase + aiStep[iDim], aiResolution[iDim])
		sample(func, aBounds, aiResolution, aiSample, aBest, dCache)
		# wiggle down and sample
		aiSample[iDim] = max(iBase - aiStep[iDim], 0)
		sample(func, aBounds, aiResolution, aiSample, aBest, dCache)
		
# optimize in n-dimensional space
def optimize(func, aBounds, aiResolution, nBest):
	# stepwidth vector
	aiStep = []
	# cache for computed samples
	dCache = dict()

	# initialize stepwidth to the center of the problem	
	for iDim in range(len(aBounds)):
		aiStep.append(aiResolution[iDim] // 2 + 1)
	
	# initialize state
	fLastBest = float("inf")
	aBest = [(fLastBest, aiStep)] * nBest
	
	# obtain initial result
	sample(func, aBounds, aiResolution, aiStep, aBest, dCache)
	(fBest, aiBest) = aBest[0]
	
	bResolution = True
	while bResolution:
		while fBest < fLastBest:
			aInitialBest = list(aBest)
			fLastBest = fBest
			for (res, aiStart) in aInitialBest:
				#print("base", aiStart)
				optimize_base(func, aBounds, aiResolution, aiStart, aiStep, aBest, dCache)
		
			(fBest, aiBest) = aBest[0]
		
		#print("best:", toCoords(aBounds, aiBest, aiResolution), fBest)
		# this resolution is depleted
		# lower resolution
		
		bResolution = False
		
		# reduce largest step by factor 2
		
		iMaxDim = numpy.argmax(aiStep)
		
		if aiStep[iMaxDim] > 1:
			bResolution = True
			aiStep[iMaxDim] //= 2
		else:
			aiStep[iMaxDim] = 1
				
		fLastBest = float("inf")
	
	'''
	for key in dCache:
		afCoords = toCoords(aBounds, list(key), aiResolution)
		strCoords = str(afCoords[0])
		for fCoord in afCoords[1:]:
			strCoords += "\t" + str(fCoord)
		print(strCoords, dCache[key])
	'''
	
	(fBest, aiBest) = aBest[0]
	return toCoords(aBounds, aiBest, aiResolution)

'''
def opt_fun(afArgs):
	return afArgs[0]*math.sin(afArgs[1])-afArgs[2] * afArgs[3]
	
def sines_fun(afArgs):
	return math.sin(6.3*afArgs[0]) + math.sin(6.3*afArgs[1]) + 1.0*(math.sin(1692.145*afArgs[1]*afArgs[0]))

optimize(sines_fun, [(0,1), (0,1)], [100, 100], 20)
optimize(opt_fun, [(0,1), (0,1), (0,1), (0,1)], [10, 20, 30, 40], 20)
'''


