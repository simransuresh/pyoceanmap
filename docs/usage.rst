Usage
=====

A typical workflow merges raw hydrographic text files, computes a derived
observable, generates a grid, adds bathymetry, and objectively maps the
observable onto the grid:

.. code-block:: python

   from pyoceanmap import (
       merge_txt_to_csv,
       generate_arctic_grid,
       add_depth_to_grid,
       compute_dynamic_height,
       compute_freshwater,
       objective_map,
   )

   # 1. Merge raw hydrographic .txt files into one CSV
   merge_txt_to_csv("./data/", "merged.csv")

   # 2. Compute a derived observable (dynamic height, via TEOS-10)
   compute_dynamic_height("merged.csv", "data_points.csv")

   # 3. Generate a projected grid and attach IBCAO bathymetry
   generate_arctic_grid("grid.csv", dx=50_000)
   add_depth_to_grid("grid.csv", "grid.csv", nc_file="IBCAO_v4_2_13_400m.nc")

   # 4. Objectively map the observable onto the grid
   objective_map(
       data_csv="data_points.csv",
       grid_csv="grid.csv",
       output_csv="mapped.csv",
       target_time="2013-09-01",
       observable="Surf_DH",
   )

See ``examples/workflow.py`` and ``examples/end2end_demo.ipynb`` in the
repository for a complete, runnable version of this pipeline.

Freshwater content
-------------------

``compute_freshwater`` follows the same pattern as ``compute_dynamic_height``
and can be mapped the same way, by passing ``observable="hFW"`` (or
``"D_Siso"``) to :func:`pyoceanmap.mapping.objective_map`.
