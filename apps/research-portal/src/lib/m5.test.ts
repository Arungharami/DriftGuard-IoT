import { describe, expect, it } from "vitest";
import { auditSchema, m5Audit } from "./m5";

describe("M5 readiness evidence", () => {
  it("keeps all seven unexecuted research areas blocked", () => {
    expect(m5Audit.experiments).toHaveLength(7);
    expect(m5Audit.experiments.every((row) => row.status === "blocked" && row.blockers.length)).toBe(true);
    expect(m5Audit.milestones.filter((row) => row.status === "absent").map((row) => row.id)).toEqual(["M3", "M4"]);
  });
  it("rejects fabricated reportability, metrics or completion", () => {
    expect(auditSchema.safeParse({ ...m5Audit, reportable: true }).success).toBe(false);
    expect(auditSchema.safeParse({ ...m5Audit, metrics: { accuracy: 1 } }).success).toBe(false);
    expect(auditSchema.safeParse({ ...m5Audit, status: "complete" }).success).toBe(false);
  });
});
