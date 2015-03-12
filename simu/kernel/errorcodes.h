//Leapfrog Speakersimulation Project
//Headerfile created by Hendrik Levering
//© Hendrik Levering Februar 2015
//© Hendrik Levering Februar 2015, all rights reserved


//This headerfile includes errorcode ouputs which are used in this project


//To do:
/****************************

Errorcodes definieren und einfügen

*************************/

#ifndef ERRORCODES_H
#define ERRORCODES_H


//Common


#define FATAL_ERROR 1
#define NO_ERR 0
#define BAD_POINTER 2

//1xxx Files
#define FILE_NOT_FOUND 1000
//11xx Corrupted_File
#define CORRUPTED_FILE 1100
#define NO_CONNECTION_FOUND 1101
#define NO_ELEMENT_FOUND 1102
#define NO_SPEAKER_FOUND 1103
#define ELEMENT_EXPECTED 11021
#define DEAD_ELEMENT 1104

#define CORRUPTED_FILE_AT_SPEAKER 1110
#define CORRUPTED_DAMPING_CONSTANT 1120;

#define FILE_IS_EMPTY 1120
#define UNEXPECTED_FILE 1140

//for quasi boolean functions which return an index
//indexing starts at 0 so -1 is defined as false
#define RESULT_FALSE -1 //-1 for indexing elements

#endif