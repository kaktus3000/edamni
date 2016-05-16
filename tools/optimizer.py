#!/usr/python3



# optimize horn geometry with regard to objective function

#read horn definition file
#read optimizer input

#define initial step widths





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
optimumParams = params
fOptimum = evaluate(params)

bBreak = False

bProgress = True
while not bBreak:
	#if we don't make any progress, reduce step widths

	bBreak = True
	if not bProgress:
		#cut step width in half
		#check for minimum step width
		else:
			#if we aren't at minimum step width yet, we can go on
			bBreak = False
	
	bProgress = False
	
	#line search for one parameter
	for param in params:
		#try moving it up first
		param.value += param.step
		
		fCost = evaluate(params)
		if fCost < fOptimum:
			bProgress = True
			fOptimum = fCost

		#then try moving it down
		param.value -= param.step * 2
		
		fCost = evaluate(params)
		if fCost < fOptimum:
			bProgress = True
			fOptimum = fCost

		


