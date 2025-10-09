Model adapted from the Foraging Robots example in:
> Hustadt, U., Ozaki, A., & Dixon, C. (2020). Theorem Proving for Pointwise Metric Temporal Logic Over the Naturals via Translations. Journal of Automated Reasoning, 64(8), 1553–1610. https://doi.org/10.1007/s10817-020-09541-4

---

Metric Temporal Logic assumptions encoded in the state machine:

```
G (resting     -> F[1,TIME_R] leavingHome)
G (leavingHome -> F[2,3] randomWalk)
G (randomWalk  -> F[1,∞] homing | moveToFood)
G (moveToFood  -> F[1,∞] grabFood | homing | scanArena)
G (scanArena   -> F[1,5] homing | moveToFood | randomWalk)
G (grabFood    -> F[2,3] moveToHome)
G (moveToHome  -> F[1,TIME_D] deposit)
G (deposit     -> F[3,4] resting)
G (homing      -> F[1,TIME_D] resting)
```

In the `limit-search` variants, we force the robot to stop searching after a certain time and return home.
