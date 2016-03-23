#ifndef PROCESSING_H_INCLUDED
#define PROCESSING_H_INCLUDED

#include <string>
#include "scanner.h"
#include "semanticchecking.h"
#include ""

class Parser
{
    private:
        std::string errormsg_;
        Scanner scanner;
        TokenArray tokens;
        //SyntaxChecker checker; in function
        bool fail_;
    private:
        void scan();
        void checksyntax();
        void preparse();
        void checksemantic();
        void store();
    public:
        Parser(std::string const &filename)
        {


        }
        void getErrorMsg(std::string &msg) {msg=errormsg_;}
        bool fail() {return fail_;}
        bool fail(std::string &msg) {msg=errormsg_; return fail_;}
        bool parse();


}

#endif // PROCESSING_H_INCLUDED
