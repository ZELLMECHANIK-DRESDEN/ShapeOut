.. _sec_qg_mixed_effects:

===========================
Comparing datasets with LMM
===========================

Consider the following datasets. A treatment is applied three times at different
time points. For each treatment, a control measurement is performed.
For each measurement day, a reservoir measurement is performed additionally
for treatment and control.

- Day1: 
  
  - one sample, called "Treatment I", measured at flow rates of 0.04,
    0.08 and 0.12 µl/s and one measurement in the reservoir
  - one control, called "Control I", measured at flow rates 0.04,
    0.08 and 0.12 µl/s and one measurement in the reservoir

- Day2: 

  - two samples, called "Treatment II" and "Treatment III", measured
    at flow rates 0.04, 0.08 and 0.12 µl/s and one measurement in the reservoir
  - two controls, called "Control II" and "Control III", measured at
    flow rates 0.04, 0.08 and 0.12 µl/s and one measurement in the reservoir

Linear mixed models (LMM) allow to assign a significance to a treatment (fixed effect)
while considering the systematic bias in-between the measurement repetitions
(random effect).

We will assume that the datasets are loaded into Shape-Out and that
invalid events have been filtered (see e.g. :ref:`sec_qg_filtering`).
The *Analyze* configuration tab enables the comparison of an experiment
(control and treatment) and repetitions of the experiment using
LMM :cite:`Herbig2017`, :cite:`Herbig2018`.

- **Basic analysis:**

  Assign which measurement is a control and which is a treatment by choosing
  the option in the dropdown lists under Interpretation. Group the pairs of
  control and treatment done in one experiment, by choosing an index number,
  called Repetition. Here, Treatment I and Control I are one experiment –
  called Repetition 1, Treatment II and Control II are a repetition of the
  experiment – called Repetition 2, Treatment III and Control III are another
  repetition of the experiment – called Repetition 3.

  Press Apply to start the calculations. A text file will open to show the results.

  The most important numbers are:

  - **Fixed effects:**

    (Intercept)-Estimate
      The mean of the parameter chosen for all controls.
    
    treatment-Estimate
      The effect size of the parameter chosen between the mean
      of all controls and the mean of all treatments.

  - **Full coefficient table:**
    Shows the effect size of the parameter chosen between control and
    treatment for every single experiment.

  - **Model-Pr(>Chisq):**
    Shows the p-value and the significance of the test.


- **Differential feature analysis:**

  The LMM analysis is only applicable if the respective measurements
  show little difference in the reservoir for the feature chosen.
  For instance, if a treatment results in non-spherical cells in the reservoir,
  then the deformation recorded for the treatment might be biased towards
  higher values.
  In this case, the information of the reservoir measurement has to be
  included by means of the differential deformation :cite:`Herbig2018`.
  This can be achieved by selecting the respective reservoir measurements
  in the dropdown menu.
