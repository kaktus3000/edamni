#include "scanner.h"
#include <exception>
#include <stdlib.h>
#include <string>

bool Scanner::keyInString(const std::string & aString, const char key)
{
	if (aString.find(key)!=std::string::npos)
		return true;
	else
		return false;
}


bool Scanner::readValue(double & aDouble,unsigned int &aInt, bool &first)
{
	currentKey_+=readUntil(KEYWORDEND); //lese zahlenstring
    if (keyInString(currentKey_,DIGITSEPARATOR[0])||keyInString(currentKey_,SCIENTIFIC[0]))
	{
		first=true;
		double d;
		std::string::size_type sz;
		try
		{
			d = std::stod(currentKey_,&sz);
		}
		catch (std::exception& e)
		{
			e.what();
			aDouble=0.0;
			return false;
		}
		if (currentKey_[sz]!=0) return false;
		aDouble=d;
		return true;
	}
	else
	{
		first=false;
		int  i;
		std::string::size_type sz;
		try
		{
			i = std::stoi(currentKey_,&sz);
		}
		catch (std::exception& e)
		{
			e.what();
			aDouble=0.0;
			return false;
		}
		if (currentKey_[sz]!=0) return false;
		aInt=i;
		return true;
	}

}
bool Scanner::readString(std::string &string)
{
	std::string buffer;
	buffer=readUntil(STRINGEND); //nicht += "-zeichen soll nicht mit in den string
	char a = readNextChar();
	if (!keyInString(STRINGEND,a)) return false; //am Dateiende angelangt = abschließendes " nicht gefunden
	string =buffer;
	return true;
}

bool Scanner::scan()
{
	for (;!eof_;)
	{
		char key = readNextChar();
		currentKey_.clear();
		if (ignoreSpaces_)  //erstmal alle leeren zeichen verwerfern
		{
			if (keyInString(SPACINGS,key))
			{
				skipSpaces();
				continue;
			}
		}
		if (ignoreComments_) //check for comments to ignore
		{
			if (keyInString(COMMENTSTART,key))
			{
				skipComment();
				continue;
			}
		}
		lastLine_=line_; //store line and pos at keyword beginning
		lastPos_=pos_;
        if (keyInString(DIRECTIONMARKER,key)) //pr�fe auf zahl
        {
            currentKey_ = key;
            if (!token_.storeToken(currentKey_,0.0,0,"",lastLine_,lastPos_))// if no knowen token
                addError();
            continue;
        }
		if (keyInString(DIGIT,key)) //pr�fe auf zahl
		{
			currentKey_ = key;
			double double_ = 0.0;
			unsigned int int_=0;
			bool first_ =true;
			if (readValue(double_,int_,first_))
			{
				if (first_)
				{
					if (!token_.storeToken(TokenTypeIdentifier[TT_FLOATVALUE],double_,0,"",lastLine_,lastPos_))// if no knowen token
						addError();
				}
				else
				{
					if (!token_.storeToken(TokenTypeIdentifier[TT_INTVALUE],0,int_,"",lastLine_,lastPos_))// if no knowen token
						addError();
				}
			}
			else
				addError();
			continue;
		}
        if (keyInString(STRINGSTART,key)) //pr�fe auf zahl
        {
        	if (!readString(currentKey_))
            {
            	currentKey_="<\">expected at the end of a string";
        		lastLine_=line_; //store line and pos at keyword beginning
        		lastPos_=pos_;
                addError();
            }
            if (!token_.storeToken(TokenTypeIdentifier[TT_STRING],0.0,0,currentKey_,lastLine_,lastPos_))// if no knowen token
            {
                addError();
            }
            continue;
        }
		currentKey_ = key;
		currentKey_ +=readUntil(KEYWORDEND); //lese token
		if (!token_.storeToken(currentKey_,0.0,0,"",lastLine_,lastPos_))// if no knowen token
			addError();
	}
	token_.complete();
	return !failflag_;
}

char Scanner::readNextChar()
{
    // Am Ende der Eingabe angelangt?
    if (iter!= source_.end())
    {
		pos_++; //position in file
		if (*iter == '\n'/*0x0A*/) //==NewLine
		{
			increaseLine();
		}
		return *(iter++);
    }
	eof_ = true;
    return 0;
}

//geht die interne zeichenkette durch bis bedingung erfüllt ist, und liefert die zeichenkette zurück
// invert = false solange zeichen der zeichenkette in keys ist wird zeichen in string eingelesen gelesen
//invert = true wenn zeichen der zeichenkette  in keys ist wird aufgehört zu lesen und auch
std::string Scanner::readUntil(std::string keys,bool invert) //lie�t bis ein zeichen aus keys auftaucht oder das Ende der scannerdaten erreicht wurde
{
	std::string string="";
	string.clear();
	for (char current = readNextChar(); (!eof_) && (invert == keyInString(keys,current));current = readNextChar())
	{
		string+=current;
	}
		iter--; //set iterator one element back so it points to the first elemt after the returned string
		pos_--;
	return string;
}



void Scanner::skipComment()
{
	readUntil(COMMENTEND);
}

void Scanner::skipSpaces()
{
	readUntil(SPACINGS,true);
}

void Scanner::addError()
{
	errors_.addError(lastLine_,lastPos_,currentKey_);
	failflag_= true;
}

