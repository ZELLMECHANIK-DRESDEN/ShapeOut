Shape-Out documentation
=======================
Building the documentation of Shape-Out requires Python 3.
To install the requirements for building the documentation, run

    pip install -r requirements.txt

To compile the documentation, run

    sphinx-build . _build

Notes
=====
To view the sphinx inventory of Shape-Out, run

   python -m sphinx.ext.intersphinx 'http://shapeout.readthedocs.io/en/develop/objects.inv'
