import { z } from "zod";

/**
 * Schema for threat details
 */
const threatDetailsSchema = z.object({
  description: z
    .string()
    .describe("A detailed description of the security threat"),
  affectedProtocols: z
    .array(z.string())
    .describe("List of protocols affected by the threat"),
  affectedTokens: z
    .array(z.string())
    .describe("List of tokens affected by the threat"),
  chain: z
    .string()
    .describe("The blockchain network where the threat is present"),
  severity: z
    .enum(["low", "medium", "high", "critical"] as const)
    .describe("The severity level of the threat"),
});

/**
 * Schema for the threat analysis result
 */
export const threatAnalysisSchema = z
  .object({
    isThreat: z
      .boolean()
      .describe("Whether the signal contains a security threat"),
    threatDetails: z
      .optional(threatDetailsSchema)
      .describe("Detailed information about the threat (if isThreat is true)"),
    analysisReasoning: z
      .optional(z.string())
      .describe("Optional reasoning behind the analysis"),
  })
  .refine(
    (data) => {
      // If isThreat is true, threatDetails must be provided
      return (
        !data.isThreat || (data.isThreat && data.threatDetails !== undefined)
      );
    },
    {
      message: "Threat details must be provided when a threat is detected",
      path: ["threatDetails"],
    }
  );

export type ThreatAnalysisResult = z.infer<typeof threatAnalysisSchema>;
export type ThreatDetails = z.infer<typeof threatDetailsSchema>;

// Export as default as well
export default threatAnalysisSchema;
