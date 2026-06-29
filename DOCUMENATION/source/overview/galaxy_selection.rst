
.. _selection-methods:

Galaxy Selection
----------------

There are two ways to select your galaxy sample in RAFIKI-CGM. 

**Ranges** (``selection.method: ranges``)
    Selects all galaxies within the simulation that fall within specified galaxy property ranges. Currently cuts can be made by stellar mass, halo mass, specific star 
    formation rate, and/or whether the galaxy is central in its halo. With this selection, sample size is set by how many galaxies in a given simulation box match the properties you choose. If no galaxies fit the criteria, the pipeline won't run. 

**Matching** (``selection.method: matching``)
    Resamples the simulation to match the stellar or halo mass distribution of a comparison catalog (i.e. an observational sample). Galaxies are binned and resampled with weights corresponding 
    to the representation of their mass bin in the comparison distribution. 

    Key parameters: 

    - ``bins`` - mass bin edges used for matching distributions
    - ``n_sample`` - number of galaxies to resample (the final stack will be three times this value, one per projection direction)
    - ``match_property`` - property to match on (currently limited to ``stellar_mass`` or ``halo_mass``)

    .. note::
        Any cuts set in selection.property_ranges will also be applied before matching. This allows for cominations, for example applying a halo mass cut to exclude clusters before matching 
        an observed stellar mass distribution

    .. warning:: 
        Larger ``n_sample`` values will more closely match the comparison catalog, but the runtime will increase accordingly. See the images 
        below that show the difference in distribution matching between N=400 (~20 minute runtime) and N=1000 (~1 hour runtime).

    

