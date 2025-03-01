import { z } from "zod";

/**
 * Schema for AI-generated threat analysis results
 * Used with the generateObject method to ensure type safety
 */
export const threatAnalysisSchema = z.object({
  isThreat: z
    .boolean()
    .describe("Whether the signal describes a security threat"),
  threatDetails: z
    .object({
      description: z.string().describe("Clear explanation of the threat"),
      affectedProtocols: z
        .array(z.string())
        .describe("List of affected protocol names in our dependency graph"),
      affectedTokens: z
        .array(z.string())
        .describe("List of affected token symbols in our dependency graph"),
      chain: z.string().describe("Affected blockchain (ethereum, etc)"),
      severity: z
        .enum(["low", "medium", "high", "critical"])
        .describe("Severity level of the threat"),
    })
    .optional()
    .describe("Details about the threat, if one is detected"),
});

// Type for the threat analysis result
export type ThreatAnalysis = z.infer<typeof threatAnalysisSchema>;
