#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A Python script that uses numpy and pyper with R and the "lme4" library
to compute relations with linear mixed effects models.
Install the "lme4" library with:
    R -e "install.packages('lme4', repos='http://cran.r-project.org')"
"""
from __future__ import division, print_function, unicode_literals

import difflib

import numpy as np
import pyper

from .util import cran

DEFAULT_BS_ITER = 1000


def classify_treatment_repetition(analysis, id_ctl="co", id_trt="",
                                  id_ctl_res="", id_trt_res=""):
    """Convenience method for assigning treatment and repetition

    This method pairs treatments and repetitions in an analysis
    using the measurement titles and identifiers given as
    keyword arguments.

    Parameters
    ----------
    analysis: shapeout.analysis.Analysis
        The analysis instance to use. The titles of the individual
        measurements will be searched for the `id_*` terms.
    id_ctl: str
        Identifies a control measurement.
    id_ctl_res: str
        Identifies a control measurement in the reservoir. Set to
        an empty string to disable.
    id_trt: str
        Identifies the treatment measurement. Set to an empty
        string to use all non-control measurements as treatments.
    id_trt_res: str
        Identifies the treatment measurement in the reservoir.
        Must be set if `id_ctl_res` is used.
    """
    # sanity checks
    if id_ctl == "" and id_trt == "":
        raise ValueError("At least `id_ctl` or `id_trt` must be set!")

    idlist = []

    for mm in analysis:
        if mm.config["setup"]["chip region"] == "reservoir":
            if id_ctl_res and id_ctl_res in mm.title:
                idlist.append(["res ctl", mm])
            elif id_trt_res and id_trt_res in mm.title:
                idlist.append(["res trt", mm])
            elif id_ctl_res == "":
                idlist.append(["res ctl", mm])
            elif id_trt_res == "":
                idlist.append(["res trt", mm])
            else:
                idlist.append(["none", mm])
        else:
            if id_ctl and id_ctl in mm.title:
                idlist.append(["ctl", mm])
            elif id_trt and id_trt in mm.title:
                idlist.append(["trt", mm])
            elif id_ctl == "":
                idlist.append(["ctl", mm])
            elif id_trt == "":
                idlist.append(["trt", mm])
            else:
                idlist.append(["none", mm])

    # extract and rename treatment
    treatment = [tt for (tt, mm) in idlist]
    treatment = [tt.replace("res", "Reservoir") for tt in treatment]
    treatment = [tt.replace("ctl", "Control") for tt in treatment]
    treatment = [tt.replace("trt", "Treatment") for tt in treatment]
    treatment = [tt.replace("none", "None") for tt in treatment]

    assert len(treatment) == len(analysis)
    # identify timeunit via similarity analysis
    ctl_str = [mm.title if tt == "ctl" else "" for (tt, mm) in idlist]
    ctl_r_str = [mm.title if tt == "res ctl" else "" for (tt, mm) in idlist]
    trt_str = [mm.title if tt == "trt" else "" for (tt, mm) in idlist ]
    trt_r_str = [mm.title if tt == "res trt" else "" for (tt, mm) in idlist]
    matchids = match_similar_strings(ctl_str, trt_str, ctl_r_str, trt_r_str)
    timeunit = np.zeros(len(analysis))
    for ii, match in enumerate(matchids):
        timeunit[match[0]] = ii+1
        timeunit[match[1]] = ii+1
        if id_ctl_res or id_trt_res:
            timeunit[match[2]] = ii+1
            timeunit[match[3]] = ii+1

    # Set all non-paired treatments to "None"
    for ii, tu in enumerate(timeunit):
        if tu == 0:
            treatment[ii] = "None"
    return treatment, timeunit


def match_similar_strings(a, b, c, d):
    """Similarity analysis to identify string-matches in four lists

    Given four lists of strings a, b, c, and d. Find the
    strings that match best using similarity analysis and return
    the matching list IDs with highest similarity first. Empty
    strings are ignored.

    For instance, the lists

    a = ["peter", "hans", "", "golf"]
    b = ["gogo", "ham", "freddy", ""]
    c = ["red", "gans", "", "hugo"]
    d = ["old", "futur", "erst", "ha"]

    will return the following match IDs:

    [1, 1, 1, 3]
    [3, 0, 3, 0]
    [0, 2, 0, 2]

    which means that these words are similar:

    ["hans", "ham", "gans", "ha"]
    ["golf", "gogo", "hugo", "old"]
    ["peter", "freddy", "red", "erst"]
    """
    ratio = lambda x, y: difflib.SequenceMatcher(a=x, b=y).ratio()
    n = len(a)
    assert len(a) == len(b) == len(c) == len(d)
    # build up simliarity matrix
    smat = np.zeros((n, n, n, n))
    for ii in range(n):
        for jj in range(n):
            if a[ii] and b[jj]:
                ratij = ratio(a[ii], b[jj])
            else:
                ratij = 0
            for kk in range(n):
                if a[ii] and c[kk]:
                    ratik = ratio(a[ii], c[kk])
                else:
                    ratik = 0
                for ll in range(n):
                    if a[ii] and d[ll]:
                        ratil = ratio(a[ii], d[ll])
                    else:
                        ratil = 0
                    smat[ii, jj, kk, ll] = ratij + ratik + ratil
    # match with maxima
    matchids = []
    for _ in range(n):
        if np.max(smat) == 0:
            break
        ai, aj, ak, al = np.argwhere(smat==smat.max())[0]
        matchids.append([ai, aj, ak, al])
        smat[ai, :, :, :] = 0
        smat[:, aj, :, :] = 0
        smat[:, :, ak, :] = 0
        smat[:, :, :, al] = 0
    return matchids


def diffdef(y, yR, bs_iter=DEFAULT_BS_ITER, rs=117):
    """
    Computes bootstrapped median distributions of same size
    for two distributions of different size.

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
    # Convert to arrays
    y = np.array(y)
    yR = np.array(yR)
    # Seed random numbers that are reproducible on different machines
    prng_object = np.random.RandomState(rs)
    # Initialize median arrays
    Median = np.zeros([bs_iter, 1])
    MedianR = np.zeros([bs_iter, 1])
    # If this loop is still too slow, we could get rid of it and
    # do everything with arrays. Depends on whether we will
    # eventually run into memory problems with array sizes
    # of y*bs_iter and yR*bs_iter.
    for q in range(bs_iter):
        # Channel data:
        # Compute random indices and draw from y
        draw_y_idx = prng_object.randint(0, len(y), len(y))
        y_resample = y[draw_y_idx]
        Median[q, 0] = np.median(y_resample)
        # Reservoir data
        # Compute random indices and draw from yR
        draw_yR_idx = prng_object.randint(0, len(yR), len(yR))
        yR_resample = yR[draw_yR_idx]
        MedianR[q, 0] = np.median(yR_resample)
    return [Median, MedianR]


def linmixmod(xs, treatment, timeunit, model='lmm', RCMD=cran.rcmd):
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
        (eg. list containing "area_um" data of several measurements)
    treatment: list
        Each item is a description/identifier for a treatment. The
        enumeration matches the index of `xs`.
        treatment[i] can be 'Control', 'Treatment', 'Reservoir Control' or 
        'Reservoir Treatment'. If 'Reservoir ...' is chosen, the algorithm
        will perform a bootstrapping algorithm that removes the median from each
        Channel measurement. That means for each 'Control' or 'Treatment' has to exist
        a 'Reservoir ...' measurement. The resulting Differential deformations
        are then used in the Linear Mixed Model.
        Values of 'None' are excluded from the analysis.
    timeunit: list
        Each item is a description/identifier for a time. The
        enumeration matches the index of `xs`.
        (e.g. list containing integers "1" and "2" according to the day
        at which the content in `xs` was measured) 
        Values of '0' are excluded from the analysis.
    model: string
        'lmm': A linear mixed model will be applied
        'glmm': A generalized linear mixed model will be applied

    Returns
    -------
    (Generalized) Linear Mixed Effects Model Result: dictionary
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

    Examples
    -------
    import numpy as np
    import pyper
    from nptdms import TdmsFile
    import os

    xs = [
    [100,99,80,120,140,150,100,100,110,111,140,145], #Larger values (Channel1)
    [20,10,5,16,14,22,27,26,5,10,11,8,15,17,20,9], #Smaller values (Reservoir1)
    [115,110,90,110,145,155,110,120,115,120,120,150,100,90,100], #Larger values (Channel2)
    [30,30,15,26,24,32,37,36,15,20,21,18,25,27,30,19], #Smaller values (Reservoir2)
    [150,150,130,170,190,250,150,150,160,161,180,195,130,120,125,130,125],
    [2,1,5,6,4,2,7,6,5,10,1,8,5,7,2,9,11,8,13],
    [155,155,135,175,195,255,155,155,165,165,185, 200,135,125,130,135,140,150,135,140],
    [25,15,19,26,44,42,35,20,15,10,11,28,35,10,25,13]] 
    treatment1 = ['Control', 'Reservoir Control', 'Control', 'Reservoir Control',\
    'Treatment', 'Reservoir Treatment','Treatment', 'Reservoir Treatment']
    timeunit1 = [1, 1, 2, 2, 1, 1, 2, 2]

    #Example 1: linear mixed models on differential deformations
    Result_1 = linmixmod(xs=xs,treatment=treatment1,timeunit=timeunit1,model='lmm')

    #Result_1:Estimate=93.69375 (i.e. the average Control value is 93.69)
    #         FixedEffect=43.93 (i.e. The treatment leads to an increase)         
    #         p-Value(Likelihood Ratio Test)=0.0006026 (i.e. the increase is significant)

    #Example 2: Ordinary Linear mixed models
    #'Reservoir' measurements are now Controls
    #'Channel' measurements are Treatments
    #This does not use differential deformation in linmixmod()
    treatment2 = ['Treatment', 'Control', 'Treatment', 'Control',\
    'Treatment', 'Control','Treatment', 'Control']
    timeunit2 = [1, 1, 2, 2, 3, 3, 4, 4]
    Result_2 = linmixmod(xs=xs,treatment=treatment2,timeunit=timeunit2,model='lmm')

    #Result_2:Estimate=17.17 (i.e. the average Control value is 17.17 )
    #         FixedEffect=120.257 (i.e. The treatment leads to an increase)         
    #         p-Value(Likelihood Ratio Test)=0.00033 (i.e. the deformation
    #         increases significantly)

    #Example 3: Generalized Linear mixed models
    treatment3 = ['Treatment', 'Control', 'Treatment', 'Control',\
    'Treatment', 'Control','Treatment', 'Control']
    timeunit3 = [1, 1, 2, 2, 3, 3, 4, 4]    
    Result_3 = linmixmod(xs=xs,treatment=treatment3,timeunit=timeunit3,model='glmm')

    #Result_3:Estimate=2.71 (i.e. the average Control value is exp(2.71)=15.08)
    #         FixedEffect=2.19 (i.e. The treatment leads to an increase)         
    #         p-Value(Likelihood Ratio Test)=0.00366 (i.e. the deformation
    #         increases significantly)     
    '''

    modelfunc = "xs~treatment+(1+treatment|timeunit)"
    nullmodelfunc = "xs~(1+treatment|timeunit)"

    # Check if all input lists have the same length
    if len(xs) != len(treatment) or len(xs) != len(timeunit):
        msg = "`treatment` and `timeunit` not defined for all variables!"
        raise ValueError(msg)
        
    if len(xs) < 3:
        msg = "Linear Mixed Models require repeated measurements. " +\
              "Please select more treatment repetitions."
        raise ValueError(msg)

    # Check that names are valid
    for trt in treatment:
        if trt not in ["None",
                       "Control",
                       "Reservoir Control",
                       "Treatment",
                       "Reservoir Treatment"]:
            raise ValueError("Unknown treatment: '{}'".format(trt))

    # Remove "None"s and "0"s
    treatment = np.array(treatment)
    timeunit = np.array(timeunit)
    xs = np.array(xs)
    invalid = np.logical_or(treatment == "None", timeunit == 0)
    treatment = list(treatment[~invalid])
    timeunit = list(timeunit[~invalid])
    xs = [xi for ii, xi in enumerate(xs) if ~invalid[ii]]

    ######################Differential Deformation#############################
    # If the user selected 'Control-Reservoir' and/or 'Treatment-Reservoir'
    Median_DiffDef = []
    TimeUnit, Treatment = [], []
    if 'Reservoir Control' in treatment or 'Reservoir Treatment' in treatment:
        if model == 'glmm':
            Head_string = "GENERALIZED LINEAR MIXED MODEL ON BOOTSTAP-DISTRIBUTIONS: \n" +\
                "---Results are in log space (loglink was used)--- \n"
        if model == 'lmm':
            Head_string = "LINEAR MIXED MODEL ON BOOTSTAP-DISTRIBUTIONS: \n"
        # Find the timeunits for Control
        where_contr_ch = np.where(np.array(treatment) == 'Control')
        timeunit_contr_ch = np.array(timeunit)[where_contr_ch]
        # Find the timeunits for Treatment
        where_treat_ch = np.where(np.array(treatment) == 'Treatment')
        timeunit_treat_ch = np.array(timeunit)[where_treat_ch]

        for n in np.unique(timeunit_contr_ch):
            where_time = np.where(np.array(timeunit) == n)
            xs_n = np.array(xs)[where_time]
            treatment_n = np.array(treatment)[where_time]
            where_contr_ch = np.where(np.array(treatment_n) == 'Control')
            xs_n_contr_ch = xs_n[where_contr_ch]
            where_contr_res = np.where(
                np.array(treatment_n) == 'Reservoir Control')
            xs_n_contr_res = xs_n[where_contr_res]

            # check that corresponding Controls are selected
            if (len(where_contr_ch[0]) != 1 or
                len(where_contr_res[0]) != 1):
                msg = "Controls for channel and reservoir must be given" \
                      +" exactly once (repetition {})!".format(n)
                raise ValueError(msg)

            # Apply the Bootstraping algorithm to Controls
            y = np.array(xs_n_contr_ch)[0]
            yR = np.array(xs_n_contr_res)[0]
            [Median, MedianR] = diffdef(y, yR)
            Median_DiffDef.append(Median - MedianR)
            # TimeUnit is a number for the day or the number of the repeat
            TimeUnit.extend(np.array(n).repeat(len(Median)))
            Treatment.extend(np.array(['Control']).repeat(len(Median)))

        for n in np.unique(timeunit_treat_ch):
            where_time = np.where(np.array(timeunit) == n)
            xs_n = np.array(xs)[where_time]
            treatment_n = np.array(treatment)[where_time]
            xs_n_contr_res = xs_n[where_contr_res]
            where_treat_ch = np.where(np.array(treatment_n) == 'Treatment')
            xs_n_treat_ch = xs_n[where_treat_ch]
            where_treat_res = np.where(
                np.array(treatment_n) == 'Reservoir Treatment')
            xs_n_treat_res = xs_n[where_treat_res]

            # check that corresponding Treatments are selected
            if (len(where_treat_ch[0]) != 1 or
                len(where_treat_res[0]) != 1):
                msg = "Treatments for channel and reservoir must be given" \
                      +" exactly once (repetition {})!".format(n)
                raise ValueError(msg)

            # Apply the Bootstraping algorithm to Treatments
            y = np.array(xs_n_treat_ch)[0]
            yR = np.array(xs_n_treat_res)[0]
            [Median, MedianR] = diffdef(y, yR)
            Median_DiffDef.append(Median - MedianR)
            # TimeUnit is a number for the day or the number of the repeat
            TimeUnit.extend(np.array(n).repeat(len(Median)))
            Treatment.extend(np.array(['Treatment']).repeat(len(Median)))

        # Concat all elements in the lists
        xs = np.concatenate(Median_DiffDef)
        xs = np.array(xs).ravel()
        treatment = np.array(Treatment)
        timeunit = np.array(TimeUnit)

    else:  # If there is no 'Reservoir Channel' selected don't apply bootstrapping
        if model == 'glmm':
            Head_string = "GENERALIZED LINEAR MIXED MODEL: \n" +\
                "---Results are in log space (loglink was used)--- \n"
        if model == 'lmm':
            Head_string = "LINEAR MIXED MODEL: \n"

        for i in range(len(xs)):
            # Expand every unit in treatment and timeunit to the same length as the
            # xs[i] they are supposed to describe
            # Using the "repeat" function also characters can be handled
            treatment[i] = np.array([treatment[i]]).repeat(len(xs[i]), axis=0)
            timeunit[i] = np.array([timeunit[i]]).repeat(len(xs[i]), axis=0)

        # Concat all elements in the lists
        xs = np.concatenate(xs)
        treatment = np.concatenate(treatment)
        timeunit = np.concatenate(timeunit)

    # Open a pyper instance
    r1 = pyper.R(RCMD=RCMD)
    # try to fix unicode decode errors by forcing english
    r1('Sys.setenv(LANG = "en")')
    r1.assign("xs", xs)
    # Transfer the vectors to R
    r1.assign("treatment", treatment)
    r1.assign("timeunit", timeunit)
    # Create a dataframe which contains all the data
    r1("RTDC=data.frame(xs,treatment,timeunit)")
    # Load the necessary library for Linear Mixed Models
    lme4resp = r1("library(lme4)").decode("utf-8")
    if lme4resp.count("Error"):
        # Tell the user that something went wrong
        raise OSError("R installation at {}: {}\n".format(RCMD, lme4resp) +
                      """Please install 'lme4' via:
              {} -e "install.packages('lme4', repos='http://cran.r-project.org')
              """.format(RCMD)
                      )

    # Random intercept and random slope model
    if model == 'glmm':
        r1("Model = glmer(" + modelfunc + ",RTDC,family=Gamma(link='log'))")
        r1("NullModel = glmer(" + nullmodelfunc + ",RTDC,family=Gamma(link='log'))")
    if model == 'lmm':
        r1("Model = lmer(" + modelfunc + ",RTDC)")
        r1("NullModel = lmer(" + nullmodelfunc + ",RTDC)")

    r1("Anova = anova(Model,NullModel)")
    Model_string = r1("summary(Model)").decode("utf-8").split("\n", 1)[1]
    Anova_string = r1("Anova").decode("utf-8").split("\n", 1)[1]
    Coef_string = r1("coef(Model)").decode("utf-8").split("\n", 2)[2]
    # Cleanup output
    Coef_string = Coef_string.replace('attr(,"class")\n', '')
    Coef_string = Coef_string.replace('[1] "coef.mer"\n', '')
    #"anova" from R does a likelihood ratio test which gives a p-Value
    p = np.array(r1.get("Anova$Pr[2]"))

    # Obtain p-Value using a normal approximation
    # Extract coefficients
    r1("coefs <- data.frame(coef(summary(Model)))")
    r1("coefs$p.normal=2*(1-pnorm(abs(coefs$t.value)))")

    # Convert to array, depending on platform or R version, this is a DataFrame
    # or a numpy array, so we convert it to an array. Because on Windows the
    # result is an array with subarrays of type np.void, we must access the
    # elements with Coeffs[0][0] instead of Coeffs[0,0].
    Coeffs = np.array(r1.get("coefs"))
    # The Average value of treatment 1
    Estimate = Coeffs[0][0]
    # The Std Error of the average value of treatment 1
    StdErrorEstimate = Coeffs[0][1]
    # treatment 2 leads to a change of the Estimate by the value "FixedEffect"
    FixedEffect = Coeffs[1][0]
    StdErrorFixEffect = Coeffs[1][1]

    # Before getting effect and error for y, transform back (there happened a log transformation in the glmer)
    estim_y = np.exp(Estimate)
    #estim_y_error = abs(np.exp(Estimate+StdErrorEstimate)-np.exp(Estimate-StdErrorEstimate))
    fixef_y = np.exp(Estimate + FixedEffect) - np.exp(Estimate)
    #fixef_y_error = abs(np.exp(Estimate+StdErrorFixEffect)-np.exp(Estimate-StdErrorFixEffect))

    full_summary = Head_string + Model_string +\
        "\nCOEFFICIENT TABLE:\n" + Coef_string +\
        "\nLIKELIHOOD RATIO TEST (MODEL VS.  NULLMODEL): \n" +\
        Anova_string

    if model == "glmm":
        full_summary += "\nESTIMATE AND EFFECT TRANSFORMED BACK FROM LOGSPACE" +\
                        "\nEstimate = \t" + str(estim_y) +\
                        "\nFixed effect = \t" + str(fixef_y)

    results = {"Full Summary": full_summary,
               "p-Value (Likelihood Ratio Test)": p,
               "Estimate": Estimate,
               "Std. Error (Estimate)": StdErrorEstimate,
               "Fixed Effect": FixedEffect,
               "Std. Error (Fixed Effect)": StdErrorFixEffect}
    return results
