.. _sec_qg_youngs_modulus:


===============
Young's Modulus
===============
TODO: helpful screenshots when the new GUI is ready.

With Shape-Out it is possible to convert deformation values to values
of the Young's modulus based on the numerical simulation work for
fully elastic spheres by Mokbel et al. :cite:`Mokbel2017`.

The "Calculate" tab  allows you to obtain
the Young's modulus for the samples you selected for plotting.

Currently, the only model available is the elastic sphere.
After choosing the type of measurement medium you must set the
right temperature or – in case you choose "Other" – the correct
viscosity. For CellCarrier media, the correct viscosity is
automatically calculated according to the shear thinning
behavior as analyzed in :cite:`Herold2017`.

Once "Compute elastic modulus" is clicked, a plotting option
for the Young's modulus will become available.

.. note:: A conversion can only be carried out for deformation and
          size values in a "valid region" that will be described
          in more detail below.

Events outside this region will disappear from the plot – also
if the Young's modulus is not selected for plotting.
To plot the complete sample in those cases again, the checkbox
"remove invalid events" in the "Filter" tab needs to be unchecked.

Valid Conversion Region
-----------------------
This section is meant to guide an experimental strategy to obtain
results that can be converted to a Young's modulus. Numerical simulations
:cite:`Mokbel2017` have yielded a valid region for the conversion in
the space of deformation and cell size shown with a color gradient
for a 20 µm channel.

It is limited by regions A and B for objects too small and objects
too large for reliable conversion. It is further limited for very
small deformation values in region C. The reason for that is a very
steep increase of E with little decrease in deformation that would
yield potentially very large errors. Finally, it is limited by region
D at larger deformation. In this region, simulations did not reach
a stationary shape for the softer objects to be found there. Instead
they became more and more elongated until they disintegrated by rupturing.

Therefore, as an experimental strategy, the goal of the experiment
must be to choose the suitable channel size and to vary the flow
rate such, that the results fall well within the valid region. 

In order to make this process more comfortable, in the following,
the valid regions are shown for the four standard channel sizes
available. Those representations include an offset shift in deformation
that would be expected in the experimental results due to the
pixelation of the image as described in :cite:`Herold2017`.

The values of the Young's moduli in those regions will depend
on the specific flow rate and the viscosity of the medium :cite:`Mietke2015`.
Note that in the illustrations that follow they merely represent a
relative scaling and are not to be compared between illustrations.

