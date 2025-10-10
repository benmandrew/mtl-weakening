from __future__ import annotations

import logging

from src.logic import mtl as m
from src.marking import common

logger = logging.getLogger(__name__)


class Marking:
    def __init__(self, trace: common.Trace, formula: m.Mtl) -> None:
        assert trace.loop_start is not None
        self.trace = trace
        self.markings = trace.to_bool_markings()
        self[formula]  # pylint: disable=pointless-statement

    def get(self, f: m.Mtl, i: int) -> bool:
        return self[f][self.trace.idx(i)]

    def _get_and(self, left: m.Mtl, right: m.Mtl) -> list[bool]:
        return [
            l and r
            for l, r in zip(self[left], self[right], strict=True)  # noqa: E741
        ]

    def _get_or(self, left: m.Mtl, right: m.Mtl) -> list[bool]:
        return [
            l or r
            for l, r in zip(self[left], self[right], strict=True)  # noqa: E741
        ]

    def _get_implies(self, left: m.Mtl, right: m.Mtl) -> list[bool]:
        return [
            (not l) or r
            for l, r in zip(self[left], self[right], strict=True)  # noqa: E741
        ]

    def _get_eventually(
        self,
        operand: m.Mtl,
        interval: m.Interval,
    ) -> list[bool]:
        vs = self[operand]
        bs = [False] * len(vs)
        for i in range(len(vs)):
            right_idx = interval[1] + 1 if interval[1] is not None else len(vs)
            bs[i] = any(
                vs[self.trace.idx(j)]
                for j in range(i + interval[0], i + right_idx)
            )
        return bs

    def _get_always(self, operand: m.Mtl, interval: m.Interval) -> list[bool]:
        vs = self[operand]
        bs = [False] * len(vs)
        for i in range(len(vs)):
            right_idx = interval[1] + 1 if interval[1] is not None else len(vs)
            bs[i] = all(
                vs[self.trace.idx(j)]
                for j in range(i + interval[0], i + right_idx)
            )
        return bs

    def _get_until(
        self,
        left: m.Mtl,
        right: m.Mtl,
        interval: m.Interval,
    ) -> list[bool]:
        rights = self[right]
        lefts = self[left]
        bs = [False] * len(rights)
        for i in range(len(rights)):
            right_idx = (
                interval[1] + 1 if interval[1] is not None else len(rights) - i
            )
            for j in range(i + interval[0], i + right_idx):
                k = self.trace.idx(j)
                if rights[k]:
                    bs[i] = True
                    break
                if not lefts[k]:
                    break
        return bs

    def _get_release(
        self,
        left: m.Mtl,
        right: m.Mtl,
        interval: m.Interval,
    ) -> list[bool]:
        rights = self[right]
        lefts = self[left]
        bs = [False] * len(rights)
        for i in range(len(rights)):
            right_idx = (
                interval[1] + 1 if interval[1] is not None else len(rights) - i
            )
            for j in range(i + interval[0], i + right_idx):
                k = self.trace.idx(j)
                if not rights[k]:
                    break
                if lefts[k]:
                    bs[i] = True
                    break
        return bs

    def _get_next(self, operand: m.Mtl) -> list[bool]:
        operands = self[operand]
        return [operands[self.trace.idx(i + 1)] for i in range(len(operands))]

    def __getitem__(self, f: m.Mtl) -> list[bool]:
        if f in self.markings:
            return self.markings[f]
        if isinstance(f, m.TrueBool):
            return [True] * len(self.trace)
        if isinstance(f, m.FalseBool):
            return [False] * len(self.trace)
        if isinstance(f, m.Prop):
            msg = f"Proposition '{f}' not found in markings. "
            raise TypeError(msg)
        if isinstance(f, m.Not):
            bs = [not v for v in self[f.operand]]
        elif isinstance(f, m.And):
            bs = self._get_and(f.left, f.right)
        elif isinstance(f, m.Or):
            bs = self._get_or(f.left, f.right)
        elif isinstance(f, m.Implies):
            bs = self._get_implies(f.left, f.right)
        elif isinstance(f, m.Eventually):
            bs = self._get_eventually(f.operand, f.interval)
        elif isinstance(f, m.Always):
            bs = self._get_always(f.operand, f.interval)
        elif isinstance(f, m.Until):
            bs = self._get_until(f.left, f.right, f.interval)
        elif isinstance(f, m.Release):
            bs = self._get_release(f.left, f.right, f.interval)
        elif isinstance(f, m.Next):
            bs = self._get_next(f.operand)
        else:
            msg = f"Unsupported MTL construct: {f}"
            raise TypeError(msg)
        self.markings[f] = bs
        return bs

    def __str__(self) -> str:
        return common.bool_markings_to_str(self.markings, self.trace.loop_start)
