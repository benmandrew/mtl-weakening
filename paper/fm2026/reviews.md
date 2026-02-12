# Review 1

**1**: weak accept
In this submission the authors propose an algorithm for interval weakening of MTL formulae via counterexample traces.

The approach is novel and the comparison to related work appropriate.

The abstract provides a fitting description of the paper.

The paper is well-written and the topic is relevant.

The proofs are correct and generally easy to follow.

The authors provide an implementation for the algorithm and present results for FRET case studies.

Nevertheless, some parts should be added or improved. These are described in the comments below.

Overall, I propose (weak) acceptance of this paper.


Detailed Comments:

The abstract mentions sensor degradation as a motivation for the defined approach.

I would expect sensor degradation to lead to incorrect system inputs (changed proposition values in \pi). As this is not addressed by the algorithm, it should be removed here.

Section 1:

You should qualify for \phi':

"the strongest possible weakening of \phi, such that \phi = \phi' [and \phi' holds in M]."

Section 2:

The presentation and proofs are easy to follow.

The note about transformation of a formula with negation should include a formula to explain the equivalence for \lnot(\phi U \psi) \equiv ... (and analogously for R).

The set of interval right modifications uses the exact same symbol as the MTL release operator. This makes especially Lemma 8 unnecessarily hard to read.

Section 3:

Def. 10: "interval of [a lasso trace] \pi". You mention this in the other definitions were necessary, and it is also required here for the definition of end_\pi.

The reason for why end_\pi(a) is defined as it is only becomes clear during the following proofs.

Adding a rationale to Def 9/10 would aid comprehension.

Lemma 13: "of of" -> "of"

"Weaken" in Algorithm 1 has the expected signature. All other functions do not receive input \pi despite requiring it to evaluate \phi, \psi.

"WeakenRec" has the same problem, missing arguments \psi, \psi'.

3.2:

It is unclear where C comes from. It is mentioned that \phi can be split, but not how C, \phi, \phi' are selected from \phi when it contains multiple temporal operators.

As described, the iterative weakening might iterate every single increment separately. The possibility to optimize this by finding a "stronger" counterexample could be discussed. In 4 you mention this problem, however, it is not clear why it is solved.

Concretely, "[...] making it more likely that we make fewer calls to the model checker" assumes that the intervals from the found counterexamples differ.

Section 4:

The RQs are appropriate.

The example in 4.1 is illustrated very well.

4.2:

You mention that the MTL formula is translated to LTL, and present a case study with 1ms per state transition.
This raises the question about a possible blowup of the length of the LTL formula with successive and nested X operators.

In general I would expect the empirical evaluation to contain quantitative results for the tool, or at the very least include notes on performance and scalability wrt. the number of temporal operators, size of intervals, or identifying problem cases for \phi.

The applicability for specification design (4.1) is intuitive. It is however unclear whether the findings of 4.2 are meaningful. It concludes "nearly a third of the analyzed requirements could be weakened", but this seems to consider any requirements expressed using time bounds as possible targets for weakening.

The system degradation is a central motivator for the algorithm, but is not further clarified.

A change in time bounds, while keeping all other guarantees, including propositions and unbounded temporal properties is a very specific kind of degradation.

Does this model behavior in practice?

It is not discussed where this approach is applicable.

It requires a system where some change constitutes a "degradation". Where do we get the quantitative information about the degradation from, that is required for the algorithm?

This should be clarified in the evaluation of the case studies (esp. RQ2).

The only example of a "system degradation" in the paper is the introductory example of an elevator's motor being replaced by a slower one.

Section 5:

The conclusion is appropriate.

The future work section mentions the omission of interval left-modifications, which is good to mention, as this question also arose for me when reading the paper.

# Review 2

**-1**: weak reject
Paper Summary ------------

The paper introduces a counterexample-guided method for weakening an MTL specification. Given a system model M and an original spec \phi, assuming that M has a counterexample trace \pi for \phi, the proposal weakens the spec \phi by relaxing a modal interval in it so that the modified spec is satisfied in \pi. The procedure is iterated till the model checking passes. The paper presents a case study with some FRET specifications.

Strengths -----------

[S1] The problem of relaxing formal specs is important in pratice, and theoretically interesting too.

[S2] The technical key lemma (Lemma 11) is interesting, based on the observation that many counterexamples are lasso paths.

Weaknesses -----------

[W1] The paper's presentation leaves much to be improved. The theoretical part (Section 3) is cluttered and it is hard to follow what is the algorithm, or why it is correct (after spending some effort, I trust it is correct, though). The evaluation part (Section 4) does not clearly present what exactly was done.

[W2] The evaluation part is insufficient. Section 4.1 is demonstration; Section 4.2 does not present which system models were used, or computation time.

Overall Impressions -----------

While I see some notable strengths, the above weaknesses make me believe that the paper is not mature enough for a top venue like FM.

Discussion of other natural approaches to the same problem is missing. For example, a non-iterative approach is conceivable, where a parametric MTL formula is translated to a parametric timed automaton, which is then model-checked against a given system model. Many problems with parametric TA are undecidable anyway, so I'm not optimistic with this direct, non-iterative approach, but I believe such should discussed.

Other Comments -----------

p2, middle: different to -> different from

p3, l13: $t$-th

p3, Definition 1 and around: this idea is well-known with the name negation normal form (NNF)

p7 and later in Section 3: I believe the writing can be much improved here. Please clarify the high-level story. Please organize technical materials in a way aligned to that high-level story.

p11, l-3 "the bound": which bound?

# Review 3

**-1**: weak reject

Software running on real-world devices is designed to fulfill a given specification.

The specification is usually formulated in LTL and expresses

liveness or safety properties.

It might be beneficial to time-box such specifications with a time interval.

It is possible to express that, e.g., an elevator arrives within 30 time units instead of just stating that an elevator arrives eventually in an unknown but finite number of steps.

Therefore, MTL was developed.

However, in degrading systems, the initial specification might not hold anymore but less restrictive specification with larger time intervals might still hold and it is still useful to know whether that is the case.

Hence, the authors propose to find a new, more lenient, specification by weakening the intervals based on learned counterexamples.

## Strengths

+ The formalization is comprehensive and the proofs are intuitive.
+ There are proofs for all algorithms.
+ The motivation is clear.

## Weaknesses

- While the implementation is available on GitHub there is no
data-availability statement and no information on how to reproduce
the results.
- The presented algorithms and their descriptions have room for improvement:
- Algorithms 1, 2, and 3 make use of undefined symbols or ask for
parameters that will not be used in the future (pi is used in
Algorithms 2 and 3 but not passed, ψ △ ψ′ is passed to WeakenC
but only used in WeakenRec while WeakenRec does not have it as
input).
- Algorithm 1 is referenced only once and that after Algorithm 3
is already introduced.
While the algorithms are in principle understandable, they should
at least be referenced and explained on a high level in the text
near their introduction.
- All algorithms come with a proof but the intuitive explanations
are missing.
- The motivating example is nice but not picked up later.
Adding such an example and demonstrating one iteration of the counter-example guided approach would be very insightful.
- There are typos and unlinked references in the paper (e.g., Fig. 1.)
- Parts of the evaluation are confusing (cf. below).



The authors claim that the weakening of the specification with respect to a given implementation and real counterexamples is novel.


The idea to weaken the original specification only by adjusting the intervals is a relevant thought in the real world.

It is desired to be tolerant against reasonable performance decreases.


The presented approach is sound. The theorems are supported by proofs.


RQ1 tries to answer the question whether the new approach is useful during the design phase of a project.

In the presented case study, the designer initially assumes that the model satisfies the condition that the robot returns to resting after at least three steps.

Concluding that the designed system does not fulfill the property does not require CEGIW.

Adjusting the specification and moving from 3 to 20 time units, however, does require CEGIW.

While this is interesting to see, it is uncertain to what extent this influences the design phase.

If a customer gives me the specification that the robot needs to rest after three iterations, then weakening the specification with CEGIW is not the desired solution as the design per se is already the flaw.

Moreover, the motivation of the paper was to weaken existing specifications in degrading systems but in the proposed scenario, CEGIW is applied to a newly designed system.

At this point in reality, it is unclear whether the system has a flaw of the design and blindly adjusting the specification might be undesired.

RQ2 investigates the applicability of the tool to selected case studies.

The authors show that it is possible to weaken the requirements in 130 cases but do not go into more details.

Since it is a case study, interesting cases (with negative and positive results) should be picked and discussed.

In the current state it is hard to see the impact of the tool.

Additionally, it is unclear how CEGIW is involved in RQ2.

In its current state, the answer to RQ2 resembles more a feasibility study, i.e., checking whether there are systems where CEGIW would help but it is not shown that it does help.

Relevant related work is mentioned.
