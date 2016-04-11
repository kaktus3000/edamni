#pragma once

#include "token.h"
#include <string>
#include <vector>
#include <iostream>

#define COMMENTSTART std::string("#")
#define	COMMENTEND	 std::string("\n\r")
#define	SPACINGS	 std::string("\t\n\r ")
#define DIGIT		 std::string("0123456789")
#define ALPHANUMERIC  std::string("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
#define DIRECTIONMARKER std::string("+-")
#define DIGITSEPARATOR  std::string(".")
#define STRINGSTART  std::string("\"")
#define STRINGEND  std::string(STRINGSTART)
#define SCIENTIFIC  std::string("e")
#define KEYWORDEND std::string(COMMENTSTART+SPACINGS)

typedef std::pair<std::pair<unsigned int,unsigned int> ,std::string> ScannerError;

class ScannerErrorArray
{
	private:
		std::vector<ScannerError> errors_;
	public:
		ScannerErrorArray() {errors_.clear();}

	void addError(const ScannerError& error)
	{
		errors_.push_back(error);
	}
	void addError(std::pair<const unsigned int,const unsigned int> lineAndPos, const std::string &msg)
	{
		errors_.push_back(std::make_pair(lineAndPos,msg));
	}
	void addError(const unsigned int line, const unsigned int pos, const std::string &msg)
	{
		errors_.push_back(std::make_pair(std::make_pair(line,pos), msg));
	}
	void printErrors(std::string & buffer)
	{
		buffer.clear();
		for( std::vector<ScannerError>::iterator i = errors_.begin(); i != errors_.end() ; ++i)
		{
			buffer+="Unknown Token @Line: "+std::to_string(i->first.first)+" @Pos: "+std::to_string(i->first.second)+" Ident: "+i->second+" \n";
		}
	}
};
/*std::ostream& operator<< (std::ostream& os,  ScannerErrorArray const &errorArray)
{
    for(
        auto i = std::begin(errorArray.errors_); i != std::end(errorArray.errors_) ; ++i)
	{
		os<<"Unknown Token @Line: "<<i->first.first<<" @Pos: "<<i->first.second<<i->second<<std::endl;
	}
	return os;
}*/


class Scanner
{
    private:
        std::vector<char> source_;
        std::vector<char>::iterator iter;
        unsigned int line_; // Aktuelle Position in der Eingabe
        unsigned int pos_; // Aktuelle Position in einer Zeile
		unsigned int lastLine_;
		unsigned int lastPos_;
		ScannerErrorArray errors_;
		bool failflag_;
		bool eof_;

		TokenHandler token_;

        bool ignoreComments_;
		bool ignoreSpaces_;



		std::string currentKey_;

    public:
		Scanner(std::vector<char>& source, bool ignoreSpaces = true, bool ignoreComments = true): source_(source)
		{
			line_ = 1;
			lastLine_=line_;
			pos_  = 0;
			lastPos_= pos_;
			iter  = source_.begin();
			currentKey_.clear();
			ignoreComments_ = ignoreComments;
			ignoreSpaces_ = ignoreSpaces;
			failflag_ = false;
			if (iter==source_.end())
				eof_= true;
			else
				eof_ = false;
		}
		bool scan();
		void getErrors(ScannerErrorArray & errors) {errors =errors_;}
		Token getToken(bool &success) { return token_.getNextToken(success);}
		void printErrors(std::string & buffer)
		{
			errors_.printErrors(buffer);
		}
		bool getTokenArray(TokenArray & tArray)
		{
			return token_.getTokenArray(tArray);
		}
    private:
		std::string readUntil(const std::string keys = "",bool invert =false);
        void skipSpaces();
		void skipComment();
		char readNextChar();
		void increaseLine() {line_++;pos_=0;}
		void addError();
		bool keyInString(const std::string &aString, const char key);
		bool readValue(double & aDouble,unsigned int &aInt, bool &first);
		bool readString(std::string &string);
};
