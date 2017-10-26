import sys
import configparser
import math
import xml.etree.ElementTree as ET

'''
output file format:

<TSPSET id="value"> //name
	<RMS> <value> //wert fuer mech. verluste
	<CMS> <value> //nachgiebigkeit
	<RE> <value> //dc widerstand
	<LE> <value> //schwingspuleninduktivitaet
	<BL> <value> //
	<SD> <value> //membranflaeche
	<MMD> <value> //membranmasse ohne luftlast, wie bei hornresp

'''

#values to read and multipliers for SI units
dReadFields = [	("Rms", 1),			#kg/s
				("Cms", 1e-3),		#mm/N -> m/N
				("Re",	1),			#ohms
				("Le",	1e-6),		#uH -> H
				("BL",	1),			#N/A
				("Sd",	1e-4),		#cm^2 -> m^2
				("Mms",	1e-3)]		#gr -> kg

#20 deg, sea level (kg/m^3)
rho = 1.2041	

def calcMmd(Mms, Sd):
	r = math.sqrt(Sd / math.pi)
	m = (8.0/3.0) * rho * r**3
	return Mms - m

def parseSpeakerFile(strSpeakerFile, strOutFile):
	
	xmlTree = ET.ElementTree(ET.Element("tspset") )
	rootElem = xmlTree.getroot()

	config = configparser.ConfigParser()
	config.read(strSpeakerFile, encoding = "Latin-1")
	
	rootElem.attrib["id"] = config["Chassis"]["manufactor"] + " " + config["Chassis"]["name"]
	
	dReadValues = dict()
	
	for (fieldName, fieldMultiplier) in dReadFields:
		for section in config.sections():
			if section == "Units":
				continue
#			print("section: ", section)
			if fieldName in config[section]:
#				print("fieldName: ", fieldName)
				strValue = config[section][fieldName]
				
				orgVal = float(strValue.replace(",", "."))
				dReadValues[fieldName] = orgVal*fieldMultiplier
				
	#check if data is complete
	if len(dReadValues) != len(dReadFields):
		print("read", len(dReadValues), "of", len(dReadFields), "attributes. quitting.")
		return
		
	#calculate Mmd
	dReadValues["Mmd"] = calcMmd(dReadValues["Mms"], dReadValues["Sd"])
	dReadValues.pop("Mms")
	
	for key in dReadValues.keys():
		valueElem = ET.SubElement(rootElem, key)
		valueElem.text = str(dReadValues[key])

	#read parameters needed
	xmlTree.write(strOutFile)

infile = sys.argv[1]
outfile = sys.argv[2]

parseSpeakerFile(infile, outfile)
