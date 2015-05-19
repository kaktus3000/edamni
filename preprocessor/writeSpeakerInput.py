import sys
import configparser
import xml.etree.ElementTree as ET
import math

<TSPSET> <ID>
<RMS> <value> //wert für mech. verluste
<CMS> <value> //nachgiebigkeit
<RE> <value> //dc widerstand
<LE> <value> //schwingspuleninduktivität
<BL> <value> //
<SD> <value> //membranfläche
<MMD> <value> //membranmasse ohne luftlast, wie bei hornresp

#values to read and multipliers for SI units
read_values = [("Rms", 1), ("Cms", ), "Re", "Le", "BL", "Sd", "Mms"]


def calcMmd(Mms, Sd)
	r = math.sqrt(Sd)
	m = (8/3)*rho*r^3

def parseSpeakersToInputFile(lstrSpeakers, strOutFile):
	
	xmlTree = ET.ElementTree(ET.Element("speakers") )
	rootElem = xmlTree.getroot()

	for (strSpeakerFile, strSpeakerID) in lstrSpeakers:
		setElem = ET.SubElement(rootElem, 'tspset')
		config = configparser.ConfigParser()
		config.read(strSpeakerFile, encoding = "Latin-1")

		setElem = ET.SubElement(rootElem, 'tspset')		

		#read parameters needed

	xmlTree.write(strOutFile)

infile = sys.argv[1]
outfile = sys.argv[2]

parseSpeakersToInputFile([infile], outfile)
