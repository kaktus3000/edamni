import sys
import copy

strEquationFile = sys.argv[1]

print("-------------")
print("equation file", strEquationFile)
print("-------------")

lstrSplit = ["^", "*", "+", "-", "(", ")", "=", "/"]
dSubstitute = {	"Delta_U" : "fDeltaU",
		"Delta_V" : "fDeltaV",
		"Delta_F" : "fDeltaF",
		"dt" : "dt",
		"mms" : "pSpeaker->mms",
		"Rms" : "pSpeaker->rms",
		"K" : "pSpeaker->sms",
		"Le" : "pSpeaker->le",
		"Re" : "pSpeaker->re",
		"BL" : "pSpeaker->bl",
		"U" : "(double)fVoltage",
		"I_c" : "fCurrent",
		"I_1" : "pSpeaker->m_fI",
		"x_c" : "fPosition",
		"x_1" : "pSpeaker->m_fX",
		"v_c" : "fVelocity",
		"v_1" : "pSpeaker->m_fV",
		"Sd" : "pSpeaker->sd",
		"dp" : "(double)fPressureDiff"
		}

def split_list(string, sep):
	astrSubs = string.split(sep)
	
	astrOut = []
	
	for sub in astrSubs:
		astrOut.append(sub.strip())
		astrOut.append(sep)
	
	astrOut = astrOut[:-1]
	
	return astrOut
	
def split_multiple(string, astrSeps):
	astrIn = [string]
	for strSep in astrSeps:
		astrOut = []
		
		for strIn in astrIn:
			astrOut += split_list(strIn, strSep)
			
		astrIn = copy.deepcopy(astrOut)
		
	return astrOut
	
def zipStrings(astrList):
	strOut = ""
	for strList in astrList:
		strOut += strList
	return strOut

with open(strEquationFile, 'r') as f:
	for strLine in f:
		astrSplit = split_multiple(strLine, lstrSplit)

		astrSplitOut = []
		iIndex = 0
		# replace exponents
		while iIndex < len(astrSplit) - 1:
			
			if astrSplit[iIndex + 1] == "^":
				astrSplitOut.append(astrSplit[iIndex])
				
				for iRep in range(int(astrSplit[iIndex + 2]) - 1):
					astrSplitOut.append("*")
					astrSplitOut.append(astrSplit[iIndex])
				
				iIndex += 2
			else:
				astrSplitOut.append(astrSplit[iIndex])
				
			iIndex += 1
		
		astrSplitOut.append(astrSplit[-1])
		
		# replace elements
		for iIndex in range(len(astrSplitOut)):
			if astrSplitOut[iIndex] in dSubstitute.keys():
				astrSplitOut[iIndex] = dSubstitute[astrSplitOut[iIndex]]
		
		print(zipStrings(astrSplitOut))
				
				
