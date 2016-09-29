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

DEFAULT_BS_ITER = 1000


def diffdef(y, yR, bs_iter=DEFAULT_BS_ITER, rs=117):
    """
    Using a bootstrapping algorithm, the reservoir distribution is
    removed from the channel distribution.
    
    Parameters
    ----------
    y: 1d ndarray of length N
        Channel data
    yR: 1d ndarray of length M
        Reservoir data
    bs_iter: int
        Number of bootstrapping iterations to perform
    rs: int
        Random state seed for random number generator
    
    Returns
    -------
    median: nd array of shape (bs_iter, 1)
        Boostrap distribution of medians of y 
    median_r: nd array of shape (bs_iter, 1)
        Boostrap distribution of medians of yR 
    """
    #Seed random numbers that are reproducible on different machines
    prng_object=np.random.RandomState(rs)
    # Initialize median arrays
    Median = np.zeros([bs_iter, 1])
    MedianR = np.zeros([bs_iter, 1])
    for q in range(bs_iter):
        # Channel data:
        # Select random indices and draw from y
        draw_y_idx = prng_object.random_integers(0, len(y)-1, len(y))
        y_resample = y[draw_y_idx]
        Median[q,0] = np.median(y_resample)
        # Reservoir data
        # Select random indices and draw from yR
        draw_yR_idx = prng_object.random_integers(0, len(yR)-1, len(yR))
        yR_resample = yR[draw_yR_idx]
        MedianR[q,0] = np.median(yR_resample)
    return [Median,MedianR]


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
    
    Optionally differential deformations are computed which are then used in the
    Linear Mixed Model
    
    Parameters
    ----------
    xs: list of multiple 1D ndarrays
        Each index of `xs` contains an array of response variables.
        (eg. list containing "Area" data of several measurements)
    treatment: list
        Each item is a description/identifier for a treatment. The
        enumeration matches the index of `xs`.
        treatment[i] can be 'Control', 'Treatment', 'Reservoir Control' or 
        'Reservoir Treatment'. If 'Reservoir ...' is chosen, the algorithm
        will perform a bootstrapping algorithm that removes the median from each
        Channel measurement. That means for each 'Control' or 'Treatment' has to exist
        a 'Reservoir ...' measurement. The resulting Differential deformations
        are then used in the Linear Mixed Model
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
    from nptdms import TdmsFile
    import os

    xs = []    
    #Deformation data from 4 experiments, and Channel and Reservoir each   
    Files = [\
    '01_w1_ST'+os.sep+'M1_2us_70A_0.040000ul_s.tdms',\
    '01_w1_ST'+os.sep+'M4_2us_70A_0.120000ul_s.tdms',\
    '02_w4_MIT'+os.sep+'M1_2us_70A_0.040000ul_s.tdms',\
    '02_w4_MIT'+os.sep+'M4_2us_70A_0.120000ul_s.tdms',\
    '03_w2_ST'+os.sep+'M1_2us_70A_0.040000ul_s.tdms',\
    '03_w2_ST'+os.sep+'M4_2us_70A_0.120000ul_s.tdms',\
    '04_w5_MIT'+os.sep+'M1_2us_70A_0.040000ul_s.tdms',\
    '04_w5_MIT'+os.sep+'M4_2us_70A_0.120000ul_s.tdms']  
    for tdms in Files:
        tdms_file = TdmsFile(tdms)
        circ_chan = tdms_file.object('Cell Track', 'circularity')
        y = 1.0-circ_chan.data        
        xs.append(y)
   
    #xs[0] and xs[1] is a measurement on a HL60 in Channel and Reservoir, respectively 
    #xs[2] and xs[3] is a measurement on a HL60 in Channel and Reservoir, respectively 
    #xs[4] and xs[5] is a measurement on a HL60 in Channel and Reservoir, respectively 
    #xs[6] and xs[7] is a measurement on a HL60 in Channel and Reservoir, respectively 

    treatment1 = ['Control', 'Reservoir Control', 'Treatment', 'Reservoir Treatment',\
    'Control', 'Reservoir Control', 'Treatment', 'Reservoir Treatment']

    treatment2 = ['Control', 'Control', 'Treatment', 'Treatment',\
    'Control', 'Control', 'Treatment', 'Treatment']

    #xs[0:2] are put to Group 1
    #xs[3:5] are put to Group 2
    timeunit = [1, 1, 1, 1, 2, 2, 2, 2]
    
    Result_1 = linmixmod(xs=xs,treatment=treatment1,timeunit=timeunit)
    #Results: Estimate=0.06250 (i.e. the average Control cell has a diff.deformation 
    #         of 0.0625)
    #         FixedEffect=-0.00297 (i.e. The other three HL60 cell have a lower 
    #         diff.deformation)         
    #         p-Value(Likelihood Ratio Test)=0.2432 (i.e. there is no signif. effect)
                
    Result_2 = linmixmod(xs=xs,treatment=treatment2,timeunit=timeunit)
    #Results: Estimate=0.05356 (i.e. the average Control cell has a deformation 
    #         of 0.05356)
    #         FixedEffect=8.20e-06 (i.e. The other four HL60 cell have a higher 
    #         deformation)         
    #         p-Value(Likelihood Ratio Test)=0.99659 (i.e. there is no signif. effect)
    '''
    
    modelfunc="xs~treatment+(1+treatment|timeunit)"
    nullmodelfunc = "xs~(1+treatment|timeunit)"
    
    #Check if all input lists have the same length
    msg = "Please define treatment and Time indicator for all Experiments"
    assert len(xs)==len(treatment)==len(timeunit),msg
    msg = "Linear Mixed Models require repeated measurements. "+\
          "Please select more treatment repetitions."
    assert len(xs)>=3,msg

    ######################Differential Deformation#############################
    #If the user selected 'Control-Reservoir' and/or 'Treatment-Reservoir'
    Median_DiffDef = []
    TimeUnit,Treatment = [],[]
    if 'Reservoir Control' in treatment or 'Reservoir Treatment' in treatment:
        Head_string = "LINEAR MIXED MODEL ON BOOTSTAP-DISTRIBUTIONS: \n "         
        for n in np.unique(timeunit):
            where_time = np.where(np.array(timeunit)==n)
            xs_n = np.array(xs)[where_time]
            treatment_n = np.array(treatment)[where_time]
            where_contr_ch = np.where('Control' == np.array(treatment_n))
            xs_n_contr_ch = xs_n[where_contr_ch]
            where_contr_res = np.where('Reservoir Control' == np.array(treatment_n))
            xs_n_contr_res = xs_n[where_contr_res]
            where_treat_ch = np.where('Treatment' == np.array(treatment_n))    
            xs_n_treat_ch = xs_n[where_treat_ch]
            where_treat_res = np.where('Reservoir Treatment' == np.array(treatment_n))
            xs_n_treat_res = xs_n[where_treat_res]

            #check that corresponding Controls and a Treatments are selected
            msg="Please select 1xCh and 1xRes for Control at Repetition "+str(n)
            assert len(where_contr_ch[0])==len(where_contr_res[0])==1,msg
            msg="Please select 1xCh and 1xRes for Treatment at Repetition "+str(n)             
            assert len(where_treat_ch[0])==len(where_treat_res[0])==1,msg
           
            #Apply the Bootstraping algorithm to Controls
            y = np.array(xs_n_contr_ch)[0]
            yR = np.array(xs_n_contr_res)[0]
            [Median,MedianR] = diffdef(y,yR)   
            Median_DiffDef.append(Median - MedianR)
            TimeUnit.extend(np.array(n).repeat(len(Median)))    #TimeUnit is a number for the day or the number of the repeat
            Treatment.extend(np.array(['Control']).repeat(len(Median)))            
                
            #Apply the Bootstraping algorithm to Treatments
            y = np.array(xs_n_treat_ch)[0]
            yR = np.array(xs_n_treat_res)[0]
            [Median,MedianR] = diffdef(y,yR)               
            Median_DiffDef.append(Median - MedianR)
            TimeUnit.extend(np.array(n).repeat(len(Median)))    #TimeUnit is a number for the day or the number of the repeat
            Treatment.extend(np.array(['Treatment']).repeat(len(Median)))            

        #Concat all elements in the lists    
        xs = np.concatenate(Median_DiffDef)
        xs = np.array(xs).ravel()
        treatment = np.array(Treatment)
        timeunit = np.array(TimeUnit)          

    else: #If there is no 'Reservoir Channel' selected dont apply bootstrapping 
        Head_string = "LINEAR MIXED MODEL: \n "         
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

    results = {"Full Summary": Head_string + Model_string+ 
    "\nFULL COEFFICIENT TABLE:\n" + Coef_string + 
    "\nLIKELIHOOD RATIO TEST (MODEL VS.  NULLMODEL): \n" + 
    Anova_string,"p-Value (Likelihood Ratio Test)" : p,
    "Estimate":Estimate,"Std. Error (Estimate)":StdErrorEstimate,
    "Fixed Effect":FixedEffect,"Std. Error (Fixed Effect)":StdErrorFixEffect}
    return results
