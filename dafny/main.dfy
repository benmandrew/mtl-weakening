datatype Option<T> = None | Some(T)

datatype Mtl =
  | MtlTrue
  | MtlFalse
  | MtlVar(string)
  | MtlAnd(Mtl, Mtl)
  | MtlOr(Mtl, Mtl)
  | MtlNot(Mtl)


datatype Context =
  | CtxEmpty
  | CtxAnd(Context, Mtl)


method Aux(trace: set<(Mtl, int)>, context: Context, t: int)
  returns (r: Option<(int, int)>)
  decreases context, 0 {
  match context
  case CtxEmpty => r := Some((0, 1));
  case CtxAnd(c, f) => r := AuxAnd(trace, c, f, t);
}


method AuxAnd(trace: set<(Mtl, int)>, context: Context, formula: Mtl, t: int)
  returns (r: Option<(int, int)>)
  decreases context {
  if (formula, t) in trace {
    r := None;
  }
  r := Aux(trace, context, t);
}
