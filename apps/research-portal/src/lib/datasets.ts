/**
 * Dataset catalog exported from the Python registry (`driftguard data export-catalog`).
 * Metadata only: provenance, license terms and schema status. Never data.
 */
import { z } from "zod";

import rawCatalog from "@/data/datasets.json";

const use = z.enum(["permitted", "permission_required", "prohibited", "not_stated"]);

export const datasetSchema = z.object({
  id: z.string(),
  name: z.string(),
  publisher: z.string(),
  homepage: z.string().url(),
  description: z.string(),
  license: z.object({
    name: z.string(),
    source_url: z.string().url(),
    verified_on: z.string().nullable(),
    academic_use: use,
    commercial_use: use,
    raw_redistribution: z.enum(["permitted_with_conditions", "not_granted", "not_stated"]),
    derived_artifact_redistribution: z.enum(["permitted", "requires_review", "prohibited"]),
    attribution_required: z.boolean(),
  }),
  citations: z.array(z.object({ text: z.string(), doi: z.string().nullable() })).min(1),
  acquisition: z.object({
    method: z.enum(["manual", "kaggle"]),
    url: z.string().url(),
    kaggle_slug: z.string().nullable(),
  }),
  tables: z.array(
    z.object({
      id: z.string(),
      filename: z.string(),
      schema_status: z.enum(["provisional", "confirmed"]),
      n_columns: z.number().int(),
      n_candidate_features: z.number().int(),
      n_private_columns: z.number().int(),
      label_column: z.string(),
      attack_type_column: z.string().nullable(),
      timestamp_column: z.string().nullable(),
      fingerprint_recorded: z.boolean(),
    }),
  ),
});

export const catalogSchema = z.object({
  schema_version: z.literal(1),
  datasets: z.array(datasetSchema),
});

export type Dataset = z.infer<typeof datasetSchema>;

export const catalog = catalogSchema.parse(rawCatalog);

export const USE_LABEL: Record<string, string> = {
  permitted: "Permitted",
  permission_required: "Permission required",
  prohibited: "Prohibited",
  not_stated: "Not stated",
  permitted_with_conditions: "Permitted with conditions",
  not_granted: "Not granted",
  requires_review: "Requires review",
};
