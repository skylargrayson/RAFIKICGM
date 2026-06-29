.. _sim_options:

Simulations 
===========
The data products in RAFIKI-CGM are generated from three different simulations/simulation suites. Here we briefly summarize the differences and provide 
links for finding more information. 

.. list-table::
   :header-rows: 1
   :widths: 27 22 22 22

   * - Property
     - SIMBA
     - EAGLE
     - RAFIKI
   * - Reference Paper
     - `Dave et al. 2019 <https://ui.adsabs.harvard.edu/abs/2019MNRAS.486.2827D/abstract>`_
     - `Schaye et al. 2015 <https://ui.adsabs.harvard.edu/abs/2015MNRAS.446..521S/abstract>`_
     - `Grayson et al. 2026 <https://ui.adsabs.harvard.edu/abs/2025arXiv251019924G/abstract>`_
   * - Runs
     - Fiducial
     - Fiducial, AGNdT9
     - Suite of 9 (A-I)
   * - Box Size
     - 50 Mpc/h
     - 50 Mpccm
     - 50 Mpc/h
   * - Initial Gas Particle Mass (:math:`h^{-1} M_\odot`)
     - :math:`1.82 \times 10^7`
     - :math:`1.81 \times 10^6`
     - :math:`1.82 \times 10^7`
   * - Softening Length (:math:`h^{-1}` kpc)
     - 0.5
     - 1.8
     - 0.5
   * - Cosmology
     - Planck 2016
     - Planck 2013
     - Planck 2016

RAFIKI Simulation Suite
-----------------------

The RAFIKI (Refining AGN Feedback in Kinetic Implementations) suite was designed to explore how varying the energetic efficiency of two AGN modes in the SIMBA simulation impacts
a range of galaxy and baryon properties. More detail and first results can be found in the `simulation paper <https://ui.adsabs.harvard.edu/abs/2025arXiv251019924G/abstract>`_

The initial suite consisted of 20 runs, but only 9 were able to successfully match the z=1 GSMF, and those 9 are included in this package. 
The runs are parameterized by :math:`\epsilon_w` the energetic efficiency of the wind mode, and  :math:`\epsilon_j` the energetic efficiency of the jet mode, where:math:`\epsilon` is the 
energetic efficiency of the feedback :math:`E_{kin} = \epsilon L_{bol}`. The table below summarizes the parameters for each run included in RAFIKI-CGM. 

+------------+--------------------+---------------------+
| Simulation | :math:`\epsilon_j` | :math:`\epsilon_w`  |
+============+====================+=====================+
| RAFIKI A   | 0.1                | 0.0125              |
+------------+--------------------+---------------------+
| RAFIKI B   | 0.1                | 0.025               |
+------------+--------------------+---------------------+
| RAFIKI C   | 0.1                | 0.05                |
+------------+--------------------+---------------------+
| RAFIKI D   | 0.2                | 0.0125              |
+------------+--------------------+---------------------+
| RAFIKI E   | 0.2                | 0.025               |
+------------+--------------------+---------------------+
| RAFIKI F   | 0.2                | 0.05                |
+------------+--------------------+---------------------+
| RAFIKI G   | 0.3                | 0.0125              |
+------------+--------------------+---------------------+
| RAFIKI H   | 0.3                | 0.025               |
+------------+--------------------+---------------------+
| RAFIKI I   | 0.3                | 0.05                |
+------------+--------------------+---------------------+





