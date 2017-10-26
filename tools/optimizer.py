#!/usr/python3	
import configparser
import xml.etree.ElementTree as ET
import sys
import os
#import scipy.optimize as opt
import ndim_search

# import modules
import run_simulation
import xml2list

# optimize horn geometry with regard to objective function

#read optimizer input file
strOptimizeInput = sys.argv[1]


strOSDir = os.path.dirname(strOptimizeInput)

if strOSDir=="":
	strOSDir = "."

g_strDir = strOSDir + "/"

optimizerInputConfig = configparser.ConfigParser()
optimizerInputConfig.read(strOptimizeInput)

g_strOptimizerIni = optimizerInputConfig.get("optimize_input", "optimizer_ini")
g_strMaterialCostIni = optimizerInputConfig.get("optimize_input", "material_cost_ini")
g_strSPLCostIni = optimizerInputConfig.get("optimize_input", "spl_cost_ini")
g_strSimulationInput = optimizerInputConfig.get("optimize_input", "simulation_input")
g_strHornFile = optimizerInputConfig.get("optimize_input", "horn_file")

simulationConfig = configparser.ConfigParser()
simulationConfig.read(g_strSimulationInput)

g_strElemFile = simulationConfig.get("general", "element_file")

# generate output path
g_strOutDir = os.path.dirname(g_strSimulationInput)

if g_strOutDir=="":
	g_strOutDir = "."

g_strOutDir = g_strOutDir + "/"

g_strElementListOutput = g_strOutDir + g_strElemFile

#read optimizer input
strOptimIniFile = g_strDir + g_strOptimizerIni
print("optimizer: opening optimizer ini from", strOptimIniFile)

optimizerConfig = configparser.ConfigParser()
optimizerConfig.read(strOptimIniFile)

#define initial step widths
g_fMinLenChange = float(optimizerConfig.get("step_control", "min_len_change"))
g_fMinLenStep = float(optimizerConfig.get("step_control", "min_len_step"))
g_fMinAreaChange = float(optimizerConfig.get("step_control", "min_area_change"))
g_fMinDampingChange = float(optimizerConfig.get("step_control", "min_damping_change"))


g_fMaxIterations = optimizerConfig.get("runtime_control", "max_iterations")
g_fMaxTime = optimizerConfig.get("runtime_control", "max_time")
g_nCPUs = optimizerConfig.get("runtime_control", "cpus")

#read horn geometry
tree = ET.parse(g_strHornFile)
g_Horn = tree.getroot()

PARAM_MIN = 0
PARAM_MAX = 1
PARAM_CURR = 2
PARAM_MIN_STEP = 3
PARAM_MIN_CHANGE = 4
# [min, max, current]
g_dParams = dict()

for section in g_Horn:
	sectionID = section.attrib["id"]

	for elem in section:
		strTag = elem.tag
		if("id" in elem.attrib.keys()):
			fMinStep = g_fMinLenStep
			fMinChange = g_fMinLenChange
			if elem.tag == "damping_constant":
				fMinChange = g_fMinDampingChange
				fMinStep = 0
			elif elem.tag != "length":
				fMinChange = g_fMinAreaChange
				fMinStep = 0

			# in case of duplicate entries, this will be overwritten.
			# should be consistent though
			g_dParams[elem.attrib["id"] ] = [float(elem.attrib["min"]), float(elem.attrib["max"]), float(elem.text), fMinStep, fMinChange]
			
strHistoryFile = g_strOutDir + "optim_history.txt"
histFile = open(strHistoryFile, 'w')

for strParam in g_dParams:
	histFile.write(strParam + "\t")
histFile.write("result\n")
histFile.flush()

def writeModifiedXML(params, strModifiedXML):
	for section in g_Horn:
		for elem in section:
			if "id" in elem.attrib.keys():
				# replace value in XML structure
				elem.text = str(params[elem.attrib["id"] ][PARAM_CURR])

	# write modified XML structure
	print("optimizer: writing modified XML to", strModifiedXML)
	
	with open(strModifiedXML, 'wb') as f:
		f.write(bytes('<?xml version="1.0" encoding="UTF-8" ?>', 'utf-8'))
		tree.write(f, 'utf-8')

def evaluate(params):
	# define new geometry
	
	# find horn section id

	# check for constant cross section in fork elements
	# A1 = A2 + A3

	# check for neighboring cross-sections
	# usually we don't want hard steps at the element borders

	# approximate means within global tolerances
	
	lValues = []
	for strParam in g_dParams.keys():
		fValue = params[strParam][PARAM_CURR]
		histFile.write(str(fValue) + "\t")
		lValues.append(fValue)
			
	# dummy function
	fReturnValue = 0
	for strParam in params.keys():
		fMin = params[strParam][PARAM_MIN]
		fMax = params[strParam][PARAM_MAX]
		fRange = fMax - fMin
		fMean = .5 * (fMax + fMin)
		fDist = params[strParam][PARAM_CURR] - fMean
		fRatio = fDist / fRange
		fReturnValue += fRatio ** 2
	
	#write horn definition xml file
	strModifiedXML = g_strOutDir + "optim_out.xml"
	writeModifiedXML(params, strModifiedXML)
	
	#generate element list
	xml2list.xml2List(strModifiedXML, g_strElementListOutput, False)
	
	#check constraints by looking at generated element list
	
	#run cost function on element list

	#check for maximum cost

	#check for maximum length

	#check for maximum volume

	#run simulation
	
	#fReturnValue = run_simulation.runSimulation(g_strSimulationInput, ["python3", "../tools/lightsim.py", "0"])
	fReturnValue = run_simulation.runSimulation(g_strSimulationInput, ["../simu/Release/simu"], "")

	#calculate objective (cost) function for output
	
	# write optimizer history file
	
	histFile.write(str(fReturnValue) + "\n")
	histFile.flush()
	
	return fReturnValue


def fromProblemFunction(lParams):
	dParams = dict()
	for strParam in g_dParams.keys():
		dParams[strParam] = g_dParams[strParam]
		dParams[strParam][PARAM_CURR] = lParams[0]
		
		lParams = lParams[1:]
		
	return dParams

def problemFunction(lParams):
	dParams = fromProblemFunction(lParams)
	
	return evaluate(dParams)


bounds = []

for strParam in g_dParams.keys():
	bmin = g_dParams[strParam][PARAM_MIN]
	bmax = g_dParams[strParam][PARAM_MAX]

	bounds.append( (bmin, bmax) )

aiResolution = []
nBest = 1

for aParams in g_dParams.values():
	fMinChange = aParams[PARAM_MIN_CHANGE]
	fMinStep = aParams[PARAM_MIN_STEP]
	
	fMin = aParams[PARAM_MIN]
	fMax = aParams[PARAM_MAX]
	
	fRange = fMax - fMin
	
	if(fMinStep == 0):
		fMinStep = fMinChange * (fRange/2 + fMin)
	
	aiResolution.append( int(fRange / fMinStep) + 1)
	
	print(fMin, fMax, aiResolution[-1] )

lResult = ndim_search.optimize(problemFunction, bounds, aiResolution, nBest)

#opt_res = opt.differential_evolution(problemFunction, bounds)
#lResult = opt_res.x


g_dOptimumParams = fromProblemFunction(lResult)

'''

#optimization loop
g_dOptimumParams = dict(g_dParams)
fOptimum = evaluate(g_dOptimumParams)

bBreak = False
bProgress = True

# global step scaler
fGlobalMultiplier = 0.5

while not bBreak:
	#if we don't make any progress, reduce step widths

	print("optimizer: global step ratio:", fGlobalMultiplier)

	if not bProgress:
		print("optimizer: no progress, cutting global multiplier down")
		#cut step width in half
		fGlobalMultiplier = fGlobalMultiplier + .5 * (1.0 - fGlobalMultiplier)
		#check for minimum step width
		
		if (1.0 - fGlobalMultiplier) < g_fMinLenChange:
			bBreak = True
		#if we aren't at minimum step width yet, we can go on
		
	bProgress = False
	
	#line search for one parameter
	for param in g_dOptimumParams.keys():
			
		# check if the global step ratio is already smaller than the allowable step ratio for the parameter
		if (1.0 - fGlobalMultiplier) < g_dParams[param][PARAM_MIN_CHANGE]:
			continue
		
		bVariableProgress = True
		
		while bVariableProgress:
			bVariableProgress = False
		
			for fMultiplier in [fGlobalMultiplier, 1.0/fGlobalMultiplier]:
				#try moving the parameter around
			
				# copy parameter dictionary
				g_dSampleParams = dict()
				for strKey in g_dOptimumParams:
					g_dSampleParams[strKey] = list(g_dOptimumParams[strKey])
			
				fParam = g_dOptimumParams[param][PARAM_CURR]
				fChangedParam = fParam * fMultiplier
				#print(param, fParam, "->", fChangedParam)
			
				fDelta = abs(fParam - fChangedParam)

				# check for minimum step width
				if fDelta < g_dOptimumParams[param][PARAM_MIN_STEP]:
					continue
				
				# check for bounds
				fChangedParam = max(fChangedParam, g_dOptimumParams[param][PARAM_MIN])
				fChangedParam = min(fChangedParam, g_dOptimumParams[param][PARAM_MAX])

				# apply parameter change		
				g_dSampleParams[param][PARAM_CURR] = fChangedParam
			
				fCost = evaluate(g_dSampleParams)
				if fCost < fOptimum:
					print("optimizer: new optimum", g_dSampleParams)
					bProgress = True
					bVariableProgress = True
					fOptimum = fCost
					g_dOptimumParams = g_dSampleParams
					break

# output optimized design

'''
evaluate(g_dOptimumParams)
print("optimizer: final optimum", g_dOptimumParams)
writeModifiedXML(g_dOptimumParams, g_strHornFile + "_opt.xml")
