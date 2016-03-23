#include "syntaxchecking.h"

void SyntaxChecker::addError(TokenType const expected,TokenType const found)
{
    addError(last_,std::string(TokenTypeDescription[expected])+" expected but found: "+TokenTypeDescription[found]);
}

bool SyntaxChecker::checkConnection()
{
    last_ = tokens_.getNextToken();
    if (!((last_.returnType()==TT_PLUS)||(last_.returnType()==TT_MINUS)))
    {
        addError(TT_PLUS,last_.returnType());
        addError(TT_MINUS,last_.returnType());
        return false;
    }
    last_ = tokens_.getNextToken();
    if (last_.returnType()!=TT_INTVALUE)
    {
        addError(TT_INTVALUE,last_.returnType());
        return false;
    }
    last_ = tokens_.getNextToken();
    if (last_.returnType()!=TT_FLOATVALUE)
    {
        addError(TT_FLOATVALUE,last_.returnType());
        return false;
    }
    return true;
}
bool SyntaxChecker::checkSpeaker()
{
    /*last_ = tokens_.getNextToken(); //check ident
    if (last_.returnType()!=TT_INTVALUE)
    {
        addError(TT_INTVALUE,last_.returnType());
        return false;
    }*/
 //check first connection
    if (!checkConnection())
        return false;
 //check second connetion
     if (!checkConnection())
        return false;
    return true;
}

bool SyntaxChecker::checkMic()
{
   /* last_ = tokens_.getNextToken(); //check ident
    if (last_.returnType()!=TT_INTVALUE)
    {
        addError(TT_INTVALUE,last_.returnType());
        return false;
    }  */
   last_ = tokens_.getNextToken(); //check ident
    if (last_.returnType()!=TT_INTVALUE)
    {
        addError(TT_INTVALUE,last_.returnType());
        return false;
    }
    return true;
}

bool SyntaxChecker::checkElems()
{
    Token tempLast(tokens_.getCurrentToken());
   last_ = tokens_.getNextToken(); //check ident
    if (last_.returnType()!=TT_INTVALUE)
    {
        addError(TT_INTVALUE,last_.returnType());
        return false;
    }
    do
    {
        if (!checkConnection())
            return false;
        tempLast=tokens_.getCurrentToken();
    } while (!((tempLast.returnType()==TT_ELEM)||(tempLast.returnType()==TT_MIC)||(tempLast.returnType()==TT_SPEAKER)||(tempLast.returnType()==TT_NIL)));
    return true;
}

bool SyntaxChecker::checkHead()
{
   last_ = tokens_.getNextToken();
    if (last_.returnType()!=TT_DX)
    {
        addError(TT_DX,last_.returnType());
        return false;
    }
    last_ = tokens_.getNextToken();
    if (last_.returnType()!=TT_FLOATVALUE)
    {
        addError(TT_FLOATVALUE,last_.returnType());
        return false;
    }
    return true;
}

bool SyntaxChecker::checkTail()
{
    for(last_ = tokens_.getNextToken();last_.returnType()!=TT_NIL;last_=tokens_.getNextToken())
    {
        switch(last_.returnType())
        {
            case TT_ELEM:       checkElems();
                                break;
            case TT_MIC:        checkMic();
                                break;
            case TT_SPEAKER:    checkSpeaker();
                                break;
            default:            failFlag_=true;
                                addError(TT_ELEM,last_.returnType());
                                addError(TT_MIC,last_.returnType());
                                addError(TT_SPEAKER,last_.returnType());
                                return !failFlag_;
        }

    }
    return true;
}

bool SyntaxChecker::check()
{
    if (!checkHead())
        return false;
    if (!checkTail())
        return false;
	return !failFlag_;
}

void SyntaxChecker::addError(const Token &token,const std::string & msg)
{
	errors_.addError(token.returnLine(),token.returnPos(),msg);
	failFlag_= true;
}
