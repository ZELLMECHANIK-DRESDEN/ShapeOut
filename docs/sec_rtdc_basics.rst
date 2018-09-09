============
RT-DC Basics
============
This section conveys the basic understanding necessary for analyzing and
interpreting RT-DC data. If you have the feeling that something is not
covered here, please create an
`issue on GitHub <https://github.com/ZELLMECHANIK-DRESDEN/ShapeOut/issues/new>`__.

Working Principle
=================



Measured Quantities/Features
============================
A multitude of features can be extracted from the data recorded during an
RT-DC measurements. These features are mostly computed live during data
acquisition and stored alongside the raw data.
Here, only the most important features are covered. A full list of the
features available in ShapeOut can be found in the
:ref:`dclab documentation <dclab:sec_features>`.


Area [µm]
---------
This is the projected event area which is determined via the contour of the
binarized event image.


Deformation
-----------
The deformation describes how much an event image deviates from a
circular shape. It is defined via the circularity:

.. math::

    \text{deformation} &= 1 - \text{circularity} \\
                       &= 1 - 2 \sqrt{\pi A} / l

with the projected event area :math:`A` and the contour length of the convex hull
of the event image :math:`l`. Computing the contour length from the convex
hull avoids an overestimation due to irregular, non-convex event shapes.


.. [1] *Statistics for real-time deformability cytometry: Clustering,
       dimensionality reduction, and significance testing* by Herbig et al.,
       licensed under CC BY 4.0 :cite:`Herbig2018`.
