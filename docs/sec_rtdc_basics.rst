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
   Figure and caption credits: [1]_.

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


Area and convex area
--------------------
This is the projected event area which is determined via the contour of the
binarized event image.


Brightness
----------
(show image of brightness vs area plot from Toepfner2017)


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


.. [2] *Statistics for real-time deformability cytometry: Clustering,
       dimensionality reduction, and significance testing* by Herbig et al.,
       licensed under CC BY 4.0 :cite:`Herbig2018`.
