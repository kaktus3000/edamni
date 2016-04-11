#pragma once

#include <map>
#include <vector>
#include <string>
#include <cctype>
#include <algorithm>
#include "../kernel/pre_simtypes.h"

enum TokenType
{
	TT_DX,
	TT_ELEM,
	TT_SPEAKER,
	TT_MIC,
    TT_PLUS,
    TT_MINUS,
    TT_INTVALUE,
	TT_FLOATVALUE,
	TT_STRING,
	TT_NIL
};

static const char *TokenTypeDescription[] =
{
	"TT_DX",
	"TT_ELEM",
	"TT_SPEAKER",
	"TT_MIC",
    "TT_PLUS",
    "TT_MINUS",
    "TT_INT",
	"TT_FLOAT",
	"TT_STRING",
	"TT_NIL"
};

static const char *TokenTypeIdentifier[] =
{
	"dx",
	"e",
	"s",
	"m",
    "+",
    "-",
    "_value_float_",
	"_value_int_",
    "_value_string_",
    ""
};

struct TokenDescriptor
{
	TokenType type;
	std::string tokenDescription;
	std::string tokenIdent;
};

class Token
{
	private:
		TokenType type_;
		double fValue_;
		unsigned int iValue_;
		std::string sValue_;
		unsigned int line_;
		unsigned int pos_;
	public:
		Token(TokenType type, double fvalue,unsigned int iValue,std::string sValue, unsigned int line, unsigned int pos):
			type_(type), fValue_(fvalue),iValue_(iValue),sValue_(sValue),line_(line),pos_(pos){}
		Token(const Token& t):
			type_(t.type_),fValue_(t.fValue_),iValue_(t.iValue_),sValue_(t.sValue_),line_(t.line_),pos_(t.pos_){}
		Token& operator= (const Token &t)
		{
			type_=t.returnType();
			fValue_=t.getFValue();
			iValue_=t.getIValue();
			sValue_=t.getSValue();
			line_=t.returnLine();
			pos_=t.returnPos();
			return *this;
		}
		std::string getSValue() const
		{
			return sValue_;
		}
		double getFValue() const
		{
			return fValue_;
		}
		unsigned int getIValue ()const
		{
			return iValue_;
		}
		TokenType returnType() const
		{
			return type_;
		}
		unsigned int returnLine()const
		{
			return line_;
		}
		unsigned int returnPos() const
		{
			return pos_;
		}
};

static Token noToken(TT_NIL,0.0,0,"",0,0);

class TokenArray //speichert tokens
{
	private:
		std::vector<Token> tokens_;
		std::vector<Token>::iterator i_;
		bool arrayComplete_;
	public:
		TokenArray()
		{
			tokens_.clear();
			i_=tokens_.begin();
			arrayComplete_=false;
		}
		TokenArray(const TokenArray &tok)
		{
			tokens_=tok.tokens_;
			i_=tokens_.begin();
			arrayComplete_=true;
		}
		TokenArray& operator = (TokenArray& tok)
		{
			tokens_=tok.tokens_;
			arrayComplete_=true;
			i_=tokens_.begin();
			return *this;
		}

		bool addToken(const Token & aToken)
		{
			if (arrayComplete_) return false;
			tokens_.push_back(aToken);
			return true;
		}
		void setToComplete()
		{
			arrayComplete_=true;
			i_ = tokens_.begin();
		}
		Token getNextToken(bool& success)
		{
			success=false;
			if (!arrayComplete_) return noToken; //only allow tokenreading after it is complete
			if (i_ != tokens_.end())
			{
				success =true;
				return  *(i_++);
			}
			else
				return noToken;
		}
		Token getNextToken()
		{
			if (!arrayComplete_) return noToken; //only allow tokenreading after it is complete
			if (i_ != tokens_.end())
			{
				return  *(i_++);
			}
			else
				return noToken;
		}
        Token getCurrentToken(bool& success)
		{
			success=false;
			if (!arrayComplete_) return noToken; //only allow tokenreading after it is complete
			if (i_ != tokens_.end())
			{
				success =true;
				return  *(i_);
			}
			else
				return noToken;
		}
        Token getCurrentToken()
		{
			if (!arrayComplete_) return noToken; //only allow tokenreading after it is complete
			if (i_ != tokens_.end())
			{
				return  *(i_);
			}
			else
				return noToken;
		}
		bool isComplete() {return arrayComplete_;}
};


class TokenHandler //�berpr�ft tokens ob sie dem zielbereich entsprechen
{
	private:
		std::map<std::string,TokenType> idents_;
		TokenArray tokens_;
		void addTokenIdent (TokenType token)
		{
			idents_.insert(std::pair<std::string,TokenType>(TokenTypeIdentifier[token],token));
		}
	public:
		TokenHandler(std::vector<std::string> &idents)
		{
			addTokenIdent(TT_DX);
			addTokenIdent(TT_ELEM);
			addTokenIdent(TT_SPEAKER);
			addTokenIdent(TT_MIC);
			addTokenIdent(TT_PLUS);
			addTokenIdent(TT_MINUS);
			addTokenIdent(TT_FLOATVALUE); //_reserved expression for float values
			addTokenIdent(TT_INTVALUE); //_reserved expression for  int values
			addTokenIdent(TT_STRING); //_reserved expression for string values
		}
		TokenHandler()
		{
			addTokenIdent(TT_DX);
			addTokenIdent(TT_ELEM);
			addTokenIdent(TT_SPEAKER);
			addTokenIdent(TT_MIC);
			addTokenIdent(TT_PLUS);
			addTokenIdent(TT_MINUS);
			addTokenIdent(TT_FLOATVALUE); //_reserved expression for float values
			addTokenIdent(TT_INTVALUE); //_reserved expression for  int values
			addTokenIdent(TT_STRING); //_reserved expression for string values
		}
		bool storeToken(const std::string & ident,const double & fValue,unsigned int iValue,std::string sValue,unsigned int line, unsigned int pos) //returns true if aToken is a validity token
		{
			std::string buffer;
			buffer.resize(ident.size());
			std::transform(ident.begin(), ident.end(), buffer.begin(), [](unsigned char c) { return std::tolower(c); }); //alles auf kleinbuchstaben �ndern
			if (idents_.find(buffer)!=idents_.end()) //valides token
			{

				Token tBuffer(idents_.find(buffer)->second,fValue,iValue,sValue,line,pos);
				return tokens_.addToken(tBuffer);
			}
			return false;
		}
		void complete()
		{
			tokens_.setToComplete();
		}
		Token getNextToken(bool& success)
		{
			return tokens_.getNextToken(success);
		}
		Token getNextToken()
		{
			return tokens_.getNextToken();
		}
		bool getTokenArray(TokenArray & tArray)
		{
			if (tokens_.isComplete())
			{
				tArray=tokens_;
				return true;
			}
			else
				return false;
		}
};



