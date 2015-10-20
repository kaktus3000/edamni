/*
 * fft.h
 *
 *  Created on: 26.07.2015
 *      Author: hendrik
 */


//this header provides fft analysis for a datafield with the this of 2^n





#ifndef FFT_H_
#define FFT_H_

#include <vector>
#include <complex>
#include <iostream>
#include <valarray>

typedef std::complex<double> Complex;
typedef std::valarray<Complex> CArray;

void fft(CArray &x);

void ifft(CArray& x);

#endif /* FFT_H_ */
