export const CEFR_LEVELS = ["B1", "B2", "C1", "C2", "C2+"];

export function cefrColor(level) {
  return { B1: "#22c55e", B2: "#3b82f6", C1: "#f59e0b", C2: "#ef4444", "C2+": "#a855f7" }[level];
}
