/** Primary fluid: uniform ink layer ``-r-r-r-r`` (no ``C``). ``color-r`` is parser-only alias. */

export type FluidPrimaryInk = "r" | "g" | "b";

export function fluidShapeCodeFromInk(ink: FluidPrimaryInk): string {
  const pair = `-${ink}`;
  return pair.repeat(4);
}

export function inkFromFluidShapeCode(code: string): FluidPrimaryInk {
  const clean = code.replaceAll(/\s/g, "");
  const low = clean.toLowerCase();
  if (low.startsWith("color-") && low.length === 7) {
    const ink = low[6];
    if (ink === "r" || ink === "g" || ink === "b") {
      return ink;
    }
  }
  if (clean.length < 8 || clean.length % 2 !== 0) {
    return "r";
  }
  const pair = clean.slice(0, 2);
  if (pair[0] === "-" && "rgb".includes(pair[1] ?? "")) {
    for (let i = 0; i < clean.length; i += 2) {
      if (clean.slice(i, i + 2) !== pair) {
        return "r";
      }
    }
    return pair[1] as FluidPrimaryInk;
  }
  if (pair[0] === "C" && "rgb".includes(pair[1] ?? "")) {
    for (let i = 0; i < clean.length; i += 2) {
      if (clean.slice(i, i + 2) !== pair) {
        return "r";
      }
    }
    return pair[1] as FluidPrimaryInk;
  }
  return "r";
}
