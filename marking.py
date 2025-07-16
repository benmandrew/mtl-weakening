from typing import Optional
import collections
import mitl as m


class Marking:
    def __init__(self, state: dict):
        self.positive = set()
        self.negative = set()
        for k, v in state.items():
            if type(v) is bool:
                p = m.Prop(k)
                if v:
                    self.positive.add(p)
                else:
                    self.negative.add(p)

    def add(self, f: m.Mitl):
        if f not in self.positive and f not in self.negative:
            match f:
                case m.Prop(name):
                    raise ValueError(
                        f"Prop '{name}' does not exist in the marking"
                    )
                case m.Not(f):
                    self.add(f)
                case m.And(left, right):
                    self.add(left)
                    self.add(right)
                case m.Or(left, right):
                    self.add(left)
                    self.add(right)
                case m.Implies(left, right):
                    self.add(left)
                    self.add(right)
                case m.Eventually(f, _):
                    self.add(f)
                case m.Always(f, _):
                    self.add(f)
                case m.Until(left, right, _):
                    self.add(f)
                case _:
                    raise ValueError(f"Unsupported MITL construct: {f}")

    def __str__(self):
        pos = [m.to_string(s) for s in self.positive]
        neg = [m.to_string(s) for s in self.negative]
        return str(pos) + " " + str(neg)

    def __repr__(self):
        return self.__str__()

    def to_list(self) -> list[m.Mitl]:
        out = list(self.positive) + list(self.negative)
        return sorted(out, key=lambda f: len(m.to_string(f)))


def generate_markings(f, trace):
    cache = dict()

    def eval_f(f):
        if f in cache:
            print("bruh")
            return cache[f]
        n = len(trace)
        out = [False] * n
        match f:
            case m.Prop(name):
                out = [state[name] for state in trace]
            case m.Not(g):
                inner = eval_f(g)
                out = [not v for v in inner]
            case m.And(left, right):
                left = eval_f(left)
                right = eval_f(right)
                out = [l and r for l, r in zip(left, right)]
            case m.Or(left, right):
                left = eval_f(left)
                right = eval_f(right)
                out = [l or r for l, r in zip(left, right)]
            case m.Implies(left, right):
                left = eval_f(left)
                right = eval_f(right)
                out = [not l or r for l, r in zip(left, right)]
            case m.Eventually(g, interval):
                a, b = interval
                inner = eval_f(g)
                for t in range(n):
                    t_min = max(t + a, 0)
                    t_max = n - 1 if b is None else min(t + b, n - 1)
                    out[t] = any(inner[k] for k in range(t_min, t_max + 1))
            case m.Always(g, interval):
                a, b = interval
                inner = eval_f(g)
                for t in range(n):
                    t_min = max(t + a, 0)
                    t_max = n - 1 if b is None else min(t + b, n - 1)
                    out[t] = all(inner[k] for k in range(t_min, t_max + 1))
            case m.Until(left, right, interval):
                a, b = interval
                left = eval_f(left)
                right = eval_f(right)
                for t in range(n):
                    t_min = max(t + a, 0)
                    t_max = n - 1 if b is None else min(t + b, n - 1)
                    for k in range(t_min, t_max + 1):
                        if right[k] and all(left[j] for j in range(t, k)):
                            out[t] = True
                            break
            case _:
                raise ValueError(f"Unsupported MITL construct: {f}")
        cache[f] = out
        return out

    eval_f(f)
    return cache


def fmt_markings(markings: dict) -> str:
    out = ""
    subformulae = list(markings.keys())
    max_len = max(len(m.to_string(f)) for f in subformulae)
    for f in subformulae:
        s = m.to_string(f)
        out += f"{s:<{max_len}} : "
        for marking in markings[f]:
            if marking:
                out += "X-"
            else:
                out += " -"
        out = out[:-1]
        out += "\n"
    return out[:-1]


def periodic_trace_idx(trace: list) -> Optional[int]:
    if len(trace) == 0:
        return None
    last = trace[-1]
    for i in range(len(trace) - 2, -1, -1):
        if last == trace[i]:
            return i
    return None


def get_variable_types(trace: list):
    variable_values = collections.defaultdict(set)
    for state in trace:
        for k, v in state.items():
            variable_values[k].add(v)
    variable_types = {}
    for var, values in variable_values.items():
        if all(isinstance(v, bool) for v in values):
            variable_types[var] = "boolean"
        elif all(isinstance(v, int) for v in values):
            max_val = max(values)
            min_val = min(values)
            variable_types[var] = f"{min_val}..{max_val}"
        else:
            raise ValueError(
                f"Mixed or unsupported types for variable '{var}': {values}"
            )
    return variable_types


def generate_trace_smv(trace: list) -> str:
    num_states = len(trace)
    loop_start = periodic_trace_idx(trace)
    variable_types = get_variable_types(trace)
    lines = []
    lines.append("MODULE main")
    lines.append("VAR")
    lines.append(f"  state : 0..{num_states - 1};")
    for var, typ in variable_types.items():
        lines.append(f"  {var} : {typ};")
    lines.append("ASSIGN")
    lines.append("  init(state) := 0;")
    lines.append("  next(state) := case")
    for i in range(num_states):
        next_state = i + 1 if i < num_states - 1 else loop_start
        lines.append(f"    state = {i} : {next_state};")
    lines.append("    TRUE : state;")
    lines.append("  esac;")
    # Set init and next values for all variables
    for var in variable_types:
        lines.append(f"  init({var}) := case")
        for i, state in enumerate(trace):
            val = state[var]
            val_str = (
                "TRUE" if val is True else "FALSE" if val is False else str(val)
            )
            lines.append(f"    state = {i} : {val_str};")
        lines.append("    TRUE : FALSE;")
        lines.append("  esac;")
        lines.append(f"  next({var}) := init({var});")
    return "\n".join(lines)


def write_trace_smv(trace: list, formula: m.Mitl) -> None:
    trace_smv = generate_trace_smv(trace)
    ltlspec_smv, _ = m.generate_subformulae_smv(formula)
    with open("trace.smv", "w") as f:
        f.write(trace_smv + "\n\n" + ltlspec_smv + "\n")
