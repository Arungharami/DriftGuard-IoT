import { z } from "zod";
import raw from "@/data/m5-audit.json";

export const auditSchema = z.object({
  schema_version: z.literal(1),
  audited_on: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  base_commit: z.string().regex(/^[0-9a-f]{40}$/),
  status: z.literal("blocked"),
  reportable: z.literal(false),
  milestones: z.array(z.object({
    id: z.string(), status: z.enum(["draft", "absent"]),
    evidence: z.url(), detail: z.string().min(1),
  }).strict()).length(5),
  experiments: z.array(z.object({
    id: z.string().min(1), title: z.string().min(1), status: z.literal("blocked"),
    implementation: z.string().min(1), blockers: z.array(z.string().min(1)).min(1),
    evidence: z.enum(["docs/m5-audit.md", "docs/m5-protocol.md"]),
  }).strict()).length(7),
}).strict();

export const m5Audit = auditSchema.parse(raw);
