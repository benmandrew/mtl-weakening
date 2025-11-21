#!/bin/sh

echo "Case Study: Foraging Robots with Unlimited Searching"

FORMULA="G(resting_p -> F[1,3](resting_p))"
DE_BRUIJN="0,1"
echo "  Formula: $FORMULA"
unbuffer python3 -m src.iterative_weaken --model-checker NUXMV --model models/foraging-robots.smv --de-bruijn $DE_BRUIJN --mtl "$FORMULA" | sed 's/^/    /'

FORMULA="G((resting_p & X (!resting_p)) -> G[1,15](!resting_p))"
DE_BRUIJN="0,1"
echo "  Formula: $FORMULA"
unbuffer python3 -m src.iterative_weaken --model-checker NUXMV --model models/foraging-robots.smv --de-bruijn $DE_BRUIJN --mtl "$FORMULA" | sed 's/^/    /'


echo "Case Study: Foraging Robots with Limited Searching"

FORMULA="G(resting_p -> F[1,3](resting_p))"
DE_BRUIJN="0,1"
echo "  Formula: $FORMULA"
unbuffer python3 -m src.iterative_weaken --model-checker NUXMV --model models/foraging-robots-limit-search.smv --de-bruijn $DE_BRUIJN --mtl "$FORMULA" | sed 's/^/    /'

FORMULA="G((resting_p & X (!resting_p)) -> G[1,15](!resting_p))"
echo "  Formula: $FORMULA"
unbuffer python3 -m src.iterative_weaken --model-checker NUXMV --model models/foraging-robots-limit-search.smv --de-bruijn $DE_BRUIJN --mtl "$FORMULA" | sed 's/^/    /'


echo "Case Study: Minimal with Unlimited Looping"

FORMULA="G(a_p -> F[1,2](a_p))"
DE_BRUIJN="0,1"
echo "  Formula: $FORMULA"
unbuffer python3 -m src.iterative_weaken --model-checker NUXMV --model models/minimal.smv --de-bruijn $DE_BRUIJN --mtl "$FORMULA" | sed 's/^/    /'

FORMULA="G((a_p & X (!a_p)) -> G[1,15](!a_p))"
echo "  Formula: $FORMULA"
unbuffer python3 -m src.iterative_weaken --model-checker NUXMV --model models/minimal.smv --de-bruijn $DE_BRUIJN --mtl "$FORMULA" | sed 's/^/    /'


echo "Case Study: Minimal with Limited Looping"

FORMULA="G(a_p -> F[1,2](a_p))"
DE_BRUIJN="0,1"
echo "  Formula: $FORMULA"
unbuffer python3 -m src.iterative_weaken --model-checker NUXMV --model models/minimal-limit-search.smv --de-bruijn $DE_BRUIJN --mtl "$FORMULA" | sed 's/^/    /'

FORMULA="G((a_p & X (!a_p)) -> G[1,15](!a_p))"
DE_BRUIJN="0,1"
echo "  Formula: $FORMULA"
unbuffer python3 -m src.iterative_weaken --model-checker NUXMV --model models/minimal-limit-search.smv --de-bruijn $DE_BRUIJN --mtl "$FORMULA" | sed 's/^/    /'
