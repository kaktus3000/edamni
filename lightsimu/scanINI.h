/*
 * Scan a typical ini file
 * - sections
 * - comment lines
 * - key/value pairs
 *
 * - no nested sections
 * - no in-line comments
 * - indents are flattened
 */


#ifndef INPUT_SCANINI_H_
#define INPUT_SCANINI_H_

#include <string>
#include <set>
#include <map>
#include <fstream>

class ScanINI
{
public:
	ScanINI(std::ifstream& iniFile);

	const std::set<std::string> getSections();
	const std::set<std::string> getKeys(const std::string& strSection);
	const std::string getKey(const std::string& strSection, const std::string& strKey);
private:
	bool scanAsSection(const std::string& strLine, std::string& strSection);
	bool scanAsComment(const std::string& strLine);
	bool scanAsKeyValue(const std::string& strLine, std::string& strKey, std::string& strValue);

	std::string stripWhitespace(const std::string& str);

	std::map<std::string, std::map<std::string, std::string>> m_mmstrValues;
};



#endif /* INPUT_SCANINI_H_ */
