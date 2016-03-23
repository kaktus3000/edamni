#pragma once

#include "token.h"
#include "scanner.h"

class SyntaxChecker //this class will test the grammatik of the token array
{
	private:
		TokenArray tokens_;
		Token last_;
		bool failFlag_;
		ScannerErrorArray errors_;
		void addError(const Token &token,const std::string & msg);
		void addError(TokenType const expected,TokenType const found);
		bool checkHead(); //look for dx plus value
		bool checkTail(); //look for rest
		bool checkElems(); //cas elemn found
		bool checkSpeaker();
		bool checkMic();
		bool checkIdent();
		bool checkConnection();
	public:
		SyntaxChecker(TokenArray &tokens): tokens_(tokens),last_(noToken){failFlag_=false;};
		bool check();
		void getErrors(ScannerErrorArray & errors) {errors =errors_;}
		void printErrors(std::string & buffer)
		{
			errors_.printErrors(buffer);
			if (failFlag_&& (last_.returnType()==TT_NIL))
                buffer+="Unexpected end of file!\n";
		}
};
