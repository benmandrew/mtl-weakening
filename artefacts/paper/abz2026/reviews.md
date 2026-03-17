# Review 1

**2**: accept

This paper presents the concept of interval weakening on MTL formulas, leading to the development of an algorithm powered by model-checking that weakens an interval of a specification until it finds a formula that holds for the given model or until no weakening is found. Correctness and optimality of the search procedure is proven (on paper) and a rather complete example is provided.

Overall I find the paper interesting and well-written. It is rather convincing and the contribution is clear. I have, of course, a few minor complaints (detailed below), but if I may provide one above the others, it would be that the paper lacks the description of a general methodology of applying the algorithm: what is a (time-)degraded system, exactly? How and when to use your algorithm, how to select the relevant interval, etc. Although the presentation of the algorithm and correction proof is convincing, the application is a bit crude and shallow, in my opinion. You should really try to find a proper methodological scenario to illustrate your general approach (and not only your algorithm).

Apart from that, since it is completely eluded in the paper, I wonder what happens when you have multiple intervals in your formula. Can you/do you weaken all of them?

The introduction is okay, but I think you should refrain from using MTL formulas. You can describe the properties you want to establish in plain English, I think.

On the topic of related works, when I read "correct-by-construction, semantics-driven approaches" I immediately thought of [10.1007/s11761-021-00314-4](https://doi.org/10.1007/s11761-021-00314-4), which also talk about system degradation in a first-order logic context.

In the proof of Theorem 3, you say that "Inductive case $\phi U_I C$ is similar to the above $[C U_I \phi]$ case" (and similarly for case $\phi R_I C$) but this is not true, is it? You should expand the proof or condense it and provided it in your repository maybe.

Mistake in the proof of Lemma 6 (a typo probably): case 1, "we that for all $t'' \in I'$, *we have $t'' \in I$, and therefore* we have $\pi, t'' |= \psi$, and so..."

A few typos and mistakes here and there:
- "systems deployed for long periods" => "systems deployed for long periods of time"
- "over the natural numbers" => "over natural numbers" or "over the set of natural numbers"
- "We do an induction proof" => "We do a proof by induction"
- "Suppose at the start of iteration i the loop invariant holds" => "Suppose at the start of iteration i *that* the loop invariant holds"

# Review 2

**2**: accept

## Summary

The paper introduces CEGIW, an algorithm, that finds relaxations of timing bounds in MTL formulae (the MTL considered is a generalization of LTL, where temporal operators have intervals as bounds, that constraint the time points, where the formula should hold), in order to find optimally weakened formulas, which still hold on a degraded system. The iterative procedure first uses a modelchecker to obtain a counterexample trace. The algorithm described in the paper then finds the minimal weakening of the interval at a single temporal operator, i.e. Until or Release, until the formula holds on the counterexample trace. This is then iterated, until either the model checker confirms, that the formula holds on the model, or the algorithm determines, that no suitable weakening exists for the trace and terminates.

In general, the correctness proof of the algorithm is convincing and a number of case studies exemplify the algorithm. Also the artifact on github is easy to use and well documented.

A weakness of the algorithm is, that it is not suitable for formulas, which need to be weakened on two or more intervals, in order to be satisfiable. Also it is unclear how the efficiency compares to other approaches.

In summary I recommend to accept this paper.

## Detailed Comments

Section 1:
In line of "Related work", "set" should be plural.

Section 2:
In the definition of Release, the indices of $\phi$ should be the other way around. In addition, I think the formula that defines R in terms of U should be added.

Before Definition 2:
This statement is trivial, since one can always choose $C = [-]$ and $\psi = \phi$. I think, what the sentence is trying to say, is that one can extract an arbitrary subformula of $\phi$ into some $\psi$ with a context $C$.

Lemma 7 and 8:
The lemmas construct two separate total orders on $B_R(I)$, but both of them seem to just be the usual subset on sets of natural numbers. Therefore, the lemmas could just use the regular subset relation.

Definition 9:
$|\pi|$ is only well-defined, if $\pi_{pre}$ and $\pi_{suf}$ are chosen to be minimal. This can easily be added to the definition.

Section 3.1, last paragraph:
At first glance, the runtime exponential in $td(\phi)$ sounds very inefficient. The paper could briefly mention, that $td(\phi)$ is generally small in practice, and give an intuition as to why the algorithm is sufficiently efficient.

Section 3.2:
I think the paper would be easier to understand, if the order of sections 3.1 and 3.2 are swapped, because this would clear up earlier, where the context $C$ and trace $\pi$ come from, which are both fixed parameters of Algorithm 1.

How is the interval to be weakened determined? There may be formulas, where only the weakening of some specific intervals leads to a formula that holds on a model.

Section 4:

I played around with the code on github and tried combining formula (16) and (19)
with a conjunction, which results in the formula `(G(resting_p -> F[1,3](resting_p)))
& (G((resting_p & X !resting_p) -> G[1,20](!resting_p)))` that needs to be weakened
on two intervals at once and the algorithm could not find a solution, when weakening
on either of the two intervals. In general, there may be more complicated examples,
which can not easily be split into two subformulas.

Fig. 4 (a): The algorithm already needs 5 iterations for a relatively simple model
and formula, is that common for interval extensions? In the extreme case, every
iteration may only expand the interval by a single time step.

# Review 3

**1**: weak accept

## Summary

This paper proposes an automated approach to interval weakening, i.e. to derive weakier time properties than the original properties from the same system model. The aim is to target the verification of long-living systems that may experience performance degradation that affects timing guarantees, even when their functional behavior remains unchanged. Timing guarantees are expressed using Metric Temporal Logic (MTL). An iterative, counterexample-guided algorithm, called Counterexample-Guided Interval Weakening (CEGIW), is presented for automatically weakening timing intervals in MTL specifications so that they hold for a given system model. Given a system model and an MTL timing property that fails on that model, the CEGIW algorithm automatically weakens the timing intervals (preserving formula structure) until the weakest/optimal weakening that holds is found. The approach uses counterexamples from a model checker (lasso traces) to drive local interval adjustments and repeats model-checking iteratively until a valid weakening is found or none exists. The paper proves correctness and optimality, evaluates the method on a running robot example and discusses its applicability on other real-world requirements/case studies. Artefacts/proofs are available in a public repository.

## Comments

Overall, the work is valuable and well grounded. A practical technique with clear motivation is proposed, useful when timing guarantees degrade but weaker bounds remain meaningful. The formal definitions, lemmas and correctness/optimality proofs appear strong, and the paper shows practical usefulness via the robot example and discusses real-world applicability on other case studies. However, some key points that affect clarity remain, especially on the Algorithm definition:

- How exactly does "weakening on a counterexample" follow from the theorems in Sect.2 (Sect.3.1)? The intuition behind this is left unclear.
- Algorithm 1 is not fully self-contained. What is the missing piece at the part marked "..." at line 7?
- The iterative loop (in the second part, Algorithm 2) depends on model-checker counterexamples and on a BMC bound (user-chosen). The paper notes this and that BMC completeness thresholds exist, but it lacks practical guidance (how to pick bounds, expected iteration counts) and instrumentation data (e.g., number of model-checker calls in the experiments). So, what's the practical stopping / repetition criteria of the iterative loop? How is the "finite end" endπ(a) is chosen/used in practice beyond the lasso definition?
- Lack of exemplification for definitions: the paper does not provide concrete, step-by-step exemplifications of many core definitions that would help readers internalize the algorithm.

## Typos/minor comments

Introduction: doesn’t -> does not
Sect. 4: Reference "operator [7, Remark 5.15]" is unclear.
