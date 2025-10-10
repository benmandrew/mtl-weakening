from __future__ import annotations

import typing

from src.logic import mtl as m
from src.marking import common


class ExtendedBoolList:
    """A list of booleans that returns True for out-of-bounds indices on the right."""

    def __init__(self, lst: list[bool]) -> None:
        self.lst = lst

    def __getitem__(self, i: int) -> bool:
        if i >= len(self.lst):
            return True
        return self.lst[i]

    def __setitem__(self, i: int, v: bool) -> None:
        if i < len(self.lst):
            self.lst[i] = v

    def __len__(self) -> int:
        return len(self.lst)

    def __iter__(self) -> typing.Iterator[bool]:
        return iter(self.lst)


class Marking:
    def __init__(self, trace: common.Trace, formula: m.Mtl) -> None:
        assert trace.loop_start is None
        self.trace = trace
        self.markings = {
            k: ExtendedBoolList(v) for k, v in trace.to_bool_markings().items()
        }
        self[formula]  # pylint: disable=pointless-statement

    def get(self, f: m.Mtl, i: int) -> bool:
        return self[f][self.trace.idx(i)]

    def _get_and(self, left: m.Mtl, right: m.Mtl) -> ExtendedBoolList:
        return ExtendedBoolList(
            [
                lb and rb
                for lb, rb in zip(
                    self[left],
                    self[right],
                    strict=True,
                )
            ],
        )

    def _get_or(self, left: m.Mtl, right: m.Mtl) -> ExtendedBoolList:
        return ExtendedBoolList(
            [
                lb or rb
                for lb, rb in zip(
                    self[left],
                    self[right],
                    strict=True,
                )
            ],
        )

    def _get_implies(self, left: m.Mtl, right: m.Mtl) -> ExtendedBoolList:
        return ExtendedBoolList(
            [
                (not lb) or rb
                for lb, rb in zip(
                    self[left],
                    self[right],
                    strict=True,
                )
            ],
        )

    def _get_eventually(
        self,
        operand: m.Mtl,
        interval: m.Interval,
    ) -> ExtendedBoolList:
        vs = self[operand]
        bs = ExtendedBoolList([False] * len(vs))
        for i in range(len(vs)):
            right_idx = interval[1] + 1 if interval[1] is not None else len(vs)
            bs[i] = any(
                vs[self.trace.idx(j)]
                for j in range(i + interval[0], i + right_idx)
            )
        return bs

    def _get_always(
        self,
        operand: m.Mtl,
        interval: m.Interval,
    ) -> ExtendedBoolList:
        vs = self[operand]
        bs = ExtendedBoolList([False] * len(vs))
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
    ) -> ExtendedBoolList:
        rights = self[right]
        lefts = self[left]
        bs = ExtendedBoolList([False] * len(rights))
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
    ) -> ExtendedBoolList:
        rights = self[right]
        lefts = self[left]
        bs = ExtendedBoolList([False] * len(rights))
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

    def _get_next(self, operand: m.Mtl) -> ExtendedBoolList:
        operands = self[operand]
        return ExtendedBoolList(
            [operands[self.trace.idx(i + 1)] for i in range(len(operands))],
        )

    def __getitem__(self, f: m.Mtl) -> ExtendedBoolList:
        if f in self.markings:
            return self.markings[f]
        if isinstance(f, m.TrueBool):
            return ExtendedBoolList([True] * len(self.trace))
        if isinstance(f, m.FalseBool):
            return ExtendedBoolList([False] * len(self.trace))
        if isinstance(f, m.Prop):
            msg = f"Proposition '{f}' not found in markings. "
            raise TypeError(msg)
        if isinstance(f, m.Not):
            bs = ExtendedBoolList([not v for v in self[f.operand]])
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
        finite_markings = {k: v.lst for k, v in self.markings.items()}
        return common.bool_markings_to_str(
            finite_markings,
            self.trace.loop_start,
        )
