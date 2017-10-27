
#xml support
import xml.etree.ElementTree as ET
import sys
import copy

strSpeakerFile = sys.argv[1]
print(strSpeakerFile)

xmlTree = ET.parse(strSpeakerFile)
rootElem = xmlTree.getroot()

dSpeakerProps = dict()

for prop in rootElem:
	dSpeakerProps[prop.tag] = prop.text

print(dSpeakerProps)

# (electrical factor, BL factor)
# acoustics gets doubled anyway
dCircuits = {'parallel' : (0.5, 1.0), 'serial': (2.0, 2.0)}

lElectricalProperties = ['Le', 'Re']
lAcousticalProperties = ['Sd', 'Mmd', 'Rms']

for strCircuit in dCircuits.keys():
	fElectricalFactor, fBLFactor = dCircuits[strCircuit]
	#print('calculating', strCircuit, 'circuit')
	
	rootElemOut =  copy.deepcopy(rootElem)
	
	rootElemOut.attrib["id"] = rootElemOut.attrib["id"] + " " + strCircuit
	
	for prop in rootElemOut:
		if prop.tag in lAcousticalProperties:
			prop.text = str(2.0 * float(prop.text))
			
		if prop.tag in lElectricalProperties:
			prop.text = str(fElectricalFactor * float(prop.text))
		
		# Cms is a reciprocal property (doubling of Kms)
		if prop.tag == 'Cms':
			prop.text = str(0.5 * float(prop.text))
			
		if prop.tag == 'BL':
			prop.text = str(fBLFactor * float(prop.text))
			
	strOutFile = strSpeakerFile[:-4] + "_" + strCircuit + ".xml"
	print("writing to file", strOutFile)
	ET.ElementTree(rootElemOut).write(strOutFile)
