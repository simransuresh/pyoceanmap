Installation
============

From source
-----------

.. code-block:: bash

   git clone https://github.com/simransuresh/pyoceanmap
   cd pyoceanmap
   pip install -e .

With test/docs extras
----------------------

.. code-block:: bash

   pip install -e ".[test]"    # pytest
   pip install -e ".[docs]"    # sphinx, sphinx-rtd-theme, myst-parser

Requirements
------------

``pyoceanmap`` requires Python 3.10+ and depends on ``numpy``, ``pandas``,
``scipy``, ``gsw``, ``netCDF4``, ``pyproj``, and ``geopy``, all installed
automatically via pip.
