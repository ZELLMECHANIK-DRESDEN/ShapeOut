============
RT-DC Basics
============
This section conveys the basic understanding necessary for analyzing and
interpreting RT-DC data. If you have the feeling that something is not
covered here, please create an
`issue on GitHub <https://github.com/ZELLMECHANIK-DRESDEN/ShapeOut/issues/new>`__.

Working Principle
=================
Describe microfluidic setup; describe forces :cite:`Mietke2015`,
:cite:`Mokbel2017`; measured quantity are bright-field images as seen
in figure below; several features can be extracted for each cell, such
as area, deformation, or brightness. These can be used to visualize
populations in a subsequent analysis step.

.. figure:: figures/rtdc-setup.jpg

   Single-cell, morpho-rheological phenotyping of blood. (A) Analysis of
   whole, diluted blood. Hydrodynamic shear forces (red arrows) induce
   deformation of cells passing through a microfluidic channel (20x20 µm²)
   at speeds of more than 30 cm/s (blue arrows). (B) Representative images of
   blood cell types acquired. Scale bar is 10 µm.
   Figure and caption adapted from Toepfner et al. [1]_.

RT-DC enables a morpho-rheological (MORE) analysis of suspended cells
and can be used to identify major blood cells, characterize their pathological
changes in disease conditions :cite:`Toepfner2017`, etc...


Measured Features
=================
A multitude of features can be extracted from the data recorded during an
RT-DC measurement. These features are mostly computed live during data
acquisition and stored alongside the raw data.
Here, only the most important features are covered. A full list of the
features available in ShapeOut is maintained by the
:ref:`dclab documentation <dclab:sec_features>`.
Please note that some of the features are only available in expert mode
(accessible via the preferences menu).


Area and porosity
-----------------
The area is the projected object area which is determined via the contour of the
binarized event image. ShapeOut differentiates between two types of area,
area of the measured contour ("Measured area [px]") and area of the convex
contour ("Convex area [px]" and "Area [µm²]"). The convex contour is the
`convex hull <https://en.wikipedia.org/wiki/Convex_hull>`__ of the measured
contour and enables a quantification of porosity (convex to measured area ratio).
A porosity of 1 means that the measured contour is convex. Note that the
porosity can only assume values larger than 1. Also note that the convex
contour/area is computed on the same pixel grid as the measured contour/area
and is, as such, subject to pixelation artifacts.

  .. figure:: figures/area.png

     Visualization of porosity. (A) The measured contour (blue line) defines
     the measured area (blue shade). The convex contour (red line) results
     in an area (red shade) that is usually larger than the measured area.
     (B) The porosity is the ratio between measured and convex contour. The
     difference (the "pores") between the measured and convex areas is
     indicated in green.


Brightness
----------
Quantifying the brightness values within the image contour yields
information on object properties such as homogeneity or density.
For instance, it has been shown that the quantities "mean brightness" and
"convex area" are sufficient to identify (and count) all major blood cells
in a drop of blood :cite:`Toepfner2018`.


Deformation
-----------
The deformation describes how much an event image deviates from a
circular shape. It is defined via the circularity:

.. math::

    \text{deformation} &= 1 - \text{circularity} \\
                       &= 1 - 2 \sqrt{\pi A} / l

with the projected event area :math:`A` and the contour length of the convex hull
of the event image :math:`l`. Note thatcComputing the contour length from the convex
hull avoids an overestimation due to irregular, non-convex event shapes.



.. [1] *Detection Of Human Disease Conditions By Single-Cell Morpho-Rheological
       Phenotyping Of Whole Blood* by Toepfner et al.,
       licensed under CC BY 4.0 :cite:`Toepfner2017`.
