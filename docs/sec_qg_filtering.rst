.. _sec_qg_filtering:


========================
Excluding invalid events
========================
Filters can be used to exclude invalid events, such as cell debris,
cell doublets or larger aggregates, or cells that are not intact, from
an analysis.

- **Area:**

  The event area (the area defined by the event contour) can be used to
  filter cell aggregates (larger area), dead or degenerate cells, as well
  as cell debris (small area). Use the deformation versus area plot to
  identify exclusion candidates by clicking on an event and visualizing
  it in the event area.

  .. figure:: figures/qg_filter_area.jpg

     Examples of events with small or large areas.


- **Aspect and inertia ratio:**

  The aspect ratio of the bounding box and the inertia ratio of the contour
  can be used to filter cell aggregates and otherwise invalid events.
  For instance, an aspect ratio below 1 (elongation perpendicular to the channel
  axis) is most-likely debris and can be excluded from the analysis.
  An inertia ratio below 1 also indicates invalid events.

  .. figure:: figures/qg_filter_ratios.jpg

     Examples of events with various aspect and inertia ratios.


- **Porosity:**

  The porosity is the ratio between measured contour and the convex contour.
  Porosity is commonly used to remove events with non-physical contours,
  e.g. for cells, all events with a porosity above 1.05.

  .. figure:: figures/qg_filter_porosity.jpg

     Examples of events with various porosities.
