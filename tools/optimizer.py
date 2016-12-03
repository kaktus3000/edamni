#!/usr/python3	
import configparser
import xml.etree.ElementTree as ET
import sys
import run_simulation

# optimize horn geometry with regard to objective function

#read optimizer input file
strConfig = sys.argv[1]
strOptimizeInput = sys.argv[2]

config = configparser.ConfigParser()
config.read(strOptimizeInput)

g_strOptimizerIni = config.get("optimize_input", "optimizer_ini")
g_strMaterialCostIni = config.get("optimize_input", "material_cost_ini")
g_strSPLCostIni = config.get("optimize_input", "spl_cost_ini")
g_strHornFile = config.get("optimize_input", "horn_file")
g_strHornOptimizerFile = config.get("optimize_input", "horn_optimizer_file")

#read optimizer input

optimizerConfig = configparser.ConfigParser()
optimizerConfig.read(g_strOptimizerIni)

#define initial step widths
g_fMinLenChange = float(optimizerConfig.get("step_control", "min_len_change"))
g_fMinLenStep = float(optimizerConfig.get("step_control", "min_len_step"))
g_fMinAreaChange = float(optimizerConfig.get("step_control", "min_area_change"))

g_fMaxIterations = optimizerConfig.get("runtime_control", "max_iterations")
g_fMaxTime = optimizerConfig.get("runtime_control", "max_time")
g_nCPUs = optimizerConfig.get("runtime_control", "cpus")

#read horn geometry
tree = ET.parse(g_strHornFile)
g_Horn = tree.getroot()

g_CurrParams = dict()

for section in g_Horn:
	sectionID = section.attrib["id"]

	for elem in section:
		strTag = elem.tag
		if strTag == "a1" or strTag == "a2" or strTag == "a3" or strTag == "length":
			g_CurrParams[sectionID + "." + strTag] = float(elem.text)

print(g_CurrParams)


def evaluate(params):
	#define new geometry
	

	#check for constant cross section in fork elements
	#A1 = A2 + A3

	#check for neighboring cross-sections
	#usually we don't want hard steps at the element borders


	#check if we already have a similar design in our cache
	#if we do, discard this design and try something different

	#approximate is within global tolerances
	
	#cache hit: we ain't got time for that
	print(params)
	return float("inf")
	
	#write horn definition xml file
	
	#generate element list

	#check constraints by looking at generated element list
	
	#run cost function on element list

	#check for maximum cost

	#check for maximum length

	#check for maximum volume

	#run simulation

	#calculate objective (cost) function for output
	
	
#optimization loop
g_OptimumParams = g_CurrParams
fOptimum = evaluate(g_OptimumParams)

bBreak = False
bProgress = True

fGlobalMultiplier = 0.5

while not bBreak:
	#if we don't make any progress, reduce step widths

	bBreak = True
	if not bProgress:
		#cut step width in half
		fGlobalMultiplier = fGlobalMultiplier + .5 * (1.0 - fGlobalMultiplier)
		#check for minimum step width
		
		if (1.0 - fGlobalMultiplier) < g_fMinLenChange:
			bBreak = True
		else:
			#if we aren't at minimum step width yet, we can go on
			bBreak = False
	
	bProgress = False
	
	#line search for one parameter
	for param in g_OptimumParams.keys():
		
		for fMultiplier in [fGlobalMultiplier, 1/fGlobalMultiplier]:
			#try moving the parameter around
			g_CurrParams = g_OptimumParams
			
			fParam = g_CurrParams[param]
			fChangedParam = fParam * fMultiplier
			
			fDelta = abs(fParam - fChangedParam)
			#check for minimum step width
			if param[-2:-1] == "a":
				if (1.0 - fGlobalMultiplier) < g_fMinAreaChange:
					continue
			else:
				if fDelta < g_fMinLenStep:
					continue
			
			g_CurrParams[param] = fChangedParam
			
			fCost = evaluate(g_CurrParams)
			if fCost < fOptimum:
				bProgress = True
				fOptimum = fCost
				g_OptimumParams = g_CurrParams

