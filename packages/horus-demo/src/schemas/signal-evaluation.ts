import { z } from "zod";

/**
 * Zod schema for validating the LLM response to a security threat evaluation.
 * This ensures the response matches the expected SignalEvaluationResult structure.
 */

// Define the severity level enum based on the existing SeverityLevel type
const SeverityLevelSchema = z.enum([
  "low",
  "medium",
  "high",
  "critical",
] as const);

// Define the threat schema
const ThreatSchema = z.object({
  description: z.string().min(1, "Description must not be empty"),
  affectedProtocols: z.array(z.string()),
  affectedTokens: z.array(z.string()),
  chain: z.string().min(1, "Chain must not be empty"),
  severity: SeverityLevelSchema,
});

// Define the main evaluation result schema
export const SignalEvaluationResultSchema = z.object({
  isThreat: z.boolean(),
  threat: z.union([ThreatSchema, z.undefined()]).optional(),
  error: z.instanceof(Error).optional(),
});

// Type export for TypeScript inference
export type ValidatedSignalEvaluationResult = z.infer<
  typeof SignalEvaluationResultSchema
>;

/**
 * Helper function to parse and validate LLM response
 * @param response The JSON string response from the LLM
 * @returns A validated SignalEvaluationResult object
 */
export function parseLLMResponse(
  response: string
): ValidatedSignalEvaluationResult {
  try {
    // Parse the JSON response from the LLM
    const parsedResponse = JSON.parse(response);

    // Validate against the Zod schema
    const validatedResult = SignalEvaluationResultSchema.parse(parsedResponse);

    return validatedResult;
  } catch (error) {
    console.error("Failed to parse LLM response:", error);
    return {
      isThreat: false,
      error: error instanceof Error ? error : new Error(String(error)),
    };
  }
}
