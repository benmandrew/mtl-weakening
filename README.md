# Metric Temporal Logic Weakening

Using:
- `nuXmv 2.1.0`, or
- `Spin 6.5.2`

## Tools

### `iterative_weaken.py`

Iteratively weaken an MTL formula on a model, using either `Spin` or `nuXmv`.

Example:
```bash
$ python3 -m src.iterative_weaken --model-checker spin --model model.pml --mtl 'G(a -> F[0,2](b))' --de-bruijn 0,1
```

### `analyse_cex.py`

Determine the optimal weakening of an MTL formula to satisfy a given trace.

Example:
```bash
$ python3 -m src.analyse_cex --model-checker nuxmv --mtl 'G(a -> F[0,2](b))' --de-bruijn 0,1 -- trace.xml
[0,5]
```

### `mtl2ltlspec.py`

Convert an MTL formula to LTL, and print it in the correct format for the given model checker.

Example:
```bash
$ python3 -m src.mtl2ltlspec --model-checker spin --mtl 'G(a -> F[0,2](b))'
[] ((a -> (b || X ((b || X (b))))))

$ python3 -m src.mtl2ltlspec --model-checker nuxmv --mtl 'G(a -> F[0,2](b))'
G ((a -> (b || X ((b || X (b))))))
```
