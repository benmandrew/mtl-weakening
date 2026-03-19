=====
Usage
=====

This project takes an ideal property in Metric Temporal Logic (MTL) that does not hold in the system, and weakens it by modifying the intervals of the temporal operators such that it either does hold, or deduces that no possible weakening exists.

You can run the the interval weakening algorithm on the included examples yourself by running

.. code-block:: bash

   $ docker run benmandrew/cegiw

Tools
=====


``iterative_weaken.py``
-----------------------

Iteratively weaken an MTL formula on a model

Example:

.. code-block:: bash

   $ python3 -m src.iterative_weaken --model model.pml --mtl 'G(a -> F[0,2](b))' --de-bruijn 0,1
   Bound 20: [0,2] → [0,18] in 0.26 seconds
   Bound 23: [0,18] → [0,25] in 12.64 seconds
   Bound 27: [0,25] → Final weakened interval
   Total time: 12.90 seconds

``analyse_cex.py``
------------------

Determine the optimal weakening of an MTL formula to satisfy a given trace.

Example:

.. code-block:: bash

   $ python3 -m src.analyse_cex --mtl 'G(a -> F[0,2](b))' --de-bruijn 0,1 -- trace.xml
   [0,5]


``mtl2ltlspec.py``
------------------

Convert an MTL formula to LTL, and print it in the correct format for the given model checker.

Example:

.. code-block:: bash

   $ python3 -m src.mtl2ltlspec --model-checker SPIN --mtl 'G(a -> F[0,2](b))'
   [] ((a -> (b || X ((b || X (b))))))

   $ python3 -m src.mtl2ltlspec --model-checker NUXMV --mtl 'G(a -> F[0,2](b))'
   G ((a -> (b || X ((b || X (b))))))


Tests and linting
=================

.. code-block:: bash

   # Format
   $ make fmt
   # Lint
   $ make lint
   # Run tests
   $ make test
