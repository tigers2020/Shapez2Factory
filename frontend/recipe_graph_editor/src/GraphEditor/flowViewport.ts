/** Ref holder for viewport center (avoids deprecated `MutableRefObject` import in Sonar ruleset). */
export type FlowViewportCenterRef = { current: (() => { x: number; y: number }) | null };
