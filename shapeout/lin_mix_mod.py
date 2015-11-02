#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A Python script that uses numpy and pyper with R and the "lme4" library
to compute relations with linear mixed effects models.

Install the "lme4" library with:

    R -e "install.packages('lme4', repos='http://cran.r-project.org')"

"""
from __future__ import division, print_function

import numpy as np
import pyper

from .util import cran

def linmixmod(xs, treatment, timeunit, RCMD=cran.rcmd):
    '''
    Linear Mixed-Effects Model computation for one fixed effect and one 
    random effect.
    This function uses the R packages "lme4" and "stats".
    
    The response variable is modeled using two linear mixed effect models 
    (Model and Nullmodel) of the form:
    - xs~treatment+(1+treatment|timeunit)
      (Random intercept + random slope model)
    - xs~(1+treatment|timeunit)
      (Nullmodel without the fixed effect "treatment")
    
    Both models are compared in R using "anova" (from the R-package "stats")
    which performs a likelihood ratio test to obtain the p-Value for the
    significance of the fixed effect (treatment).
    
    Parameters
    ----------
    xs: list of multiple 1D ndarrays
        Each index of `xs` contains an array of response variables.
        (eg. list containing "Area" data of several measurements)
    treatment: list
        Each item is a description/identifier for a treatment. The
        enumeration matches the index of `xs`.
        (e.g. list containing "Control" and "Data")
    timeunit: list
        Each item is a description/identifier for a time. The
        enumeration matches the index of `xs`.
        (e.g. list containing integers "1" and "2" according to the day
        at which the content in `xs` was measured)          

    Returns
    -------
    Linear Mixed Effects Model Result: dictionary
    The dictionary contains:
    -Estimate:  the average value of cells that had Treatment 1
    -Fixed Effect: Change of the estimate value due to the Treatment 2
    -Std Error for the Estimate
    -Std Error for the Fixed Effect
    -p-Value
    
    References
    ----------
    .. [1] R package "lme4":
           Bates D, Maechler M, Bolker B and Walker S (2015). lme4: Linear mixed-
           effects models using Eigen and S4. R package version 1.1-9, 
           https://CRAN.R-project.org/package=lme4.    
    
    .. [2] R function "anova" from package "stats":
           Chambers, J. M. and Hastie, T. J. (1992) Statistical Models in S, 
           Wadsworth & Brooks/Cole
    
    Example
    -------
    import numpy as np
    import pyper
    
    #Area data from 4 experiments   
    xs = [
    [100,99,80,120,140,150,100,100,110,111,140,145],
    [115,110,90,110,145,155,110,120,115,120,120,150,100,90,100],
    [150,150,130,170,190,250,150,150,160,161,180,195,130,120,125,130,125],
    [155,155,135,175,195,255,155,155,165,165,185, 200,135,125,130,135,140,150,
    135,140]
    ]
    
    #xs[0] and xs[2] was a measurement on a control sample 
    #xs[1] and xs[3] was a measurement on a drug-treated sample
    treatment = ['Control', 'Drug', 'Control', 'Drug']
    #xs[0] and xs[1] where measured on day 1
    #xs[2] and xs[3] where measured on day 2
    timeunit = [1, 1, 2, 2]
    
    linmixmod(xs=xs,treatment=treatment,timeunit=timeunit)
    #Results: Estimate=136.64 (i.e. the average Control cell has an area 
    #         of 136.64)
    #         FixedEffect=1.41 (i.e. The drug treatment leds to an increase 
    #         in area of 1.41)         
    #         p-Value(Likelihood Ratio Test)=0.84 (i.e. the Drug has not a 
    #         significant effect)
    '''
    
    modelfunc="xs~treatment+(1+treatment|timeunit)"
    nullmodelfunc = "xs~(1+treatment|timeunit)"
    
    #Check if all input lists have the same length
    if len(xs)==len(treatment)==len(timeunit): 
        pass
    else:
        raise ValueError("Please define treatment  and Time indicator for all Experiments")
    
    if len(xs)<3:
        raise ValueError("Please use Linear Mixed Models only to analyze repeated measurements. Select more measurements") 
    
    for i in range(len(xs)): 
        #Expand every unit in treatment and timeunit to the same length as the 
        #xs[i] they are supposed to describe
        #Using the "repeat" function also characters can be handled
        treatment[i] = np.array([treatment[i]]).repeat(len(xs[i]), axis=0)  
        timeunit[i] = np.array([timeunit[i]]).repeat(len(xs[i]), axis=0)
    
    #Concat all elements in the lists    
    xs = np.concatenate(xs)
    treatment = np.concatenate(treatment)
    timeunit = np.concatenate(timeunit)

    #Open a pyper instance
    r1 = pyper.R(use_pandas=True, RCMD=RCMD) 
    r1.assign("xs", xs) 
    #Transfer the vectors to R
    r1.assign("treatment", treatment)
    r1.assign("timeunit", timeunit)
    #Create a dataframe which contains all the data
    r1("RTDC=data.frame(xs,treatment,timeunit)")
    #Load the necessary library for Linear Mixed Models    
    lme4resp = r1("library(lme4)") 
    if lme4resp.count("Error"):
        # Tell the user that something went wrong
        raise OSError("R installation at {}: {}\n".format(RCMD, lme4resp)+
              """Please install 'lme4' via:
              {} -e "install.packages('lme4', repos='http://cran.r-project.org')
              """.format(RCMD)
                      )

    #Random intercept and random slope model
    r1("Model = lmer("+modelfunc+",RTDC)")
    r1("NullModel = lmer("+nullmodelfunc+",RTDC)")
    r1("Anova = anova(Model,NullModel)")
    Model_string = r1("summary(Model)")
    #Delete some first characters made by R
    Model_string= Model_string[23:]
    #in case you prefer a dict for the Model output, do:
    #Model_dict = np.array(r1.get("summary(Model)")) 
    Anova_string = r1("Anova")
    Anova_string = Anova_string[14:]
    #Anova_dict = np.array(r1.get("Anova"))
    Coef_string = r1("coef(Model)")
    Coef_string = Coef_string[20:]
    #"anova" from R does a likelihood ratio test which gives a p-Value 
    p = np.array(r1.get("Anova$Pr[2]"))

    #Obtain p-Value using a normal approximation
    #Extract coefficients
    r1("coefs <- data.frame(coef(summary(Model)))")   
    r1("coefs$p.normal=2*(1-pnorm(abs(coefs$t.value)))")

    #p_normal = np.array(r1.get("coefs$p.normal"))
    #p_normal = p_normal[1]
    
    # Convert to array, depending on platform or R version, this is a DataFrame
    # or a numpy array, so we convert it to an array. Because on Windows the
    # result is an array with subarrays of type np.void, we must access the
    # elements with Coeffs[0][0] instead of Coeffs[0,0].
    Coeffs = np.array(r1.get("coefs"))
    #The Average value of treatment 1
    Estimate = Coeffs[0][0]
    #The Std Error of the average value of treatment 1    
    StdErrorEstimate = Coeffs[0][1]
    #treatment 2 leads to a change of the Estimate by the value "FixedEffect"
    FixedEffect = Coeffs[1][0]   
    StdErrorFixEffect = Coeffs[1][1]
   
    results = {"Full Summary":"LINEAR MIXED MODEL: \n " + Model_string+ 
    "\nFULL COEFFICIENT TABLE:\n" + Coef_string + 
    "\nLIKELIHOOD RATIO TEST (MODEL VS.  NULLMODEL): \n" + 
    Anova_string,"p-Value (Likelihood Ratio Test)" : p,
    "Estimate":Estimate,"Std. Error (Estimate)":StdErrorEstimate,
    "Fixed Effect":FixedEffect,"Std. Error (Fixed Effect)":StdErrorFixEffect}
    return results
