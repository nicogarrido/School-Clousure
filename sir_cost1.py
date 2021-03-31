#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 12:44:41 2020

@author: Disco
"""

# cost function for the SIR model for python 2.7
# Marisa Eisenberg (marisae@umich.edu)
# Yu-Han Kao (kaoyh@umich.edu) -7-9-17

import numpy as np
import sir_ode
from scipy.stats import poisson
from scipy.stats import norm

from scipy.integrate import odeint as ode

def NLL(params, data, times): #negative log likelihood
	params = np.abs(params)
	data = np.array(data)
	res = ode(sir_ode.model, sir_ode.x0fcn(params,data), times, args=(params,))
	y = sir_ode.yfcn(res, params)
    # y = [i for i in y if i != 0]
    