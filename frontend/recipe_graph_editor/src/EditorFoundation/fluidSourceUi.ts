/** Pure fluid placeholder: four identical circle quadrants, primary ink only. */

export type FluidPrimaryInk = "r" | "g" | "b";

export function fluidShapeCodeFromInk(ink: FluidPrimaryInk): string {
  const quad = `C${ink}`;
  return quad.repeat(4);
}

export function inkFromFluidShapeCode(code: string): FluidPrimaryInk {
  const clean = code.replaceAll(/\s/g, "");
  if (clean.length < 8 || clean.length % 2 !== 0) {
    return "r";
  }
  const pair = clean.slice(0, 2);
  if (!pair.startsWith("C") || !"rgb".includes(pair[1] ?? "")) {
    return "r";
  }
  for (let i = 0; i < clean.length; i += 2) {
    if (clean.slice(i, i + 2) !== pair) {
      return "r";
    }
  }
  return pair[1] as FluidPrimaryInk;
}
