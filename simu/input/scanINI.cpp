#include "scanINI.h"

#include <fstream>
#include <iostream>

ScanINI::ScanINI(std::string strFileName)
{
	std::ifstream iniFile(strFileName);

	std::string strCurrSection("");
	m_mmstrValues[strCurrSection] = std::map<std::string, std::string>();

	size_t nLines = 0;

	while(!iniFile.eof())
	{
		nLines++;

		std::string strCurrLine;
		std::getline(iniFile, strCurrLine);

		std::string strStripped = stripWhitespace(strCurrLine);
		if(strStripped.length() < 2)
			continue;

		std::string strSection, strKey, strValue;
		//try to scan as section line
		if(scanAsSection(strStripped, strSection))
		{
			strCurrSection = strSection;
			m_mmstrValues[strCurrSection] = std::map<std::string, std::string>();
			continue;
		}

		if(scanAsComment(strStripped))
			continue;

		if(scanAsKeyValue(strStripped, strKey, strValue))
		{
			m_mmstrValues[strCurrSection][strKey] = strValue;
			continue;
		}
		std::cout << "ERROR parsing INI file " << strFileName << ", line " << nLines << ": \"" << strStripped << "\"\n";
	}
}

const std::set<std::string>
ScanINI::getSections()
{
}

const std::set<std::string>
ScanINI::getKeys(const std::string& strSection)
{
}

const std::string
ScanINI::getKey(const std::string& strSection, const std::string& strKey)
{
}

bool
ScanINI::scanAsSection(const std::string& strLine, std::string& strSection)
{
	//first and last chars have to be brackets
	if(strLine.front() != '[' || strLine.back() != ']')
		return false;
	strSection = strLine.substr( 1, strLine.length() - 2);
	return true;
}

bool
ScanINI::scanAsComment(const std::string& strLine)
{
	if(strLine.front() == '#')
		return true;
	return false;
}

bool
ScanINI::scanAsKeyValue(const std::string& strLine, std::string& strKey, std::string& strValue)
{
	size_t eq = strLine.find_first_of('=');
	if(eq == std::string::npos)
		return false;
	strKey = stripWhitespace(strLine.substr(0, eq));
	strValue = stripWhitespace(strLine.substr(eq + 1));
	return true;
}

std::string ScanINI::stripWhitespace(const std::string& str)
{
	size_t first = str.find_first_not_of(" \t");
	if( first == std::string::npos)
		return std::string ("");
	else
	{
		std::string strTrimmed(str.substr( first ));

		size_t end = strTrimmed.find_last_not_of(" \t");
		return strTrimmed.substr( 0, end + 1 );
	}
}
