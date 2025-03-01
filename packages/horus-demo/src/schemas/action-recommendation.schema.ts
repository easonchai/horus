import { z } from "zod";

/**
 * Schema for recommended action items
 */
const actionItemSchema = z.object({
  actionType: z.enum(["swap", "withdraw", "revoke"]),
  protocol: z.string().describe("The protocol name this action targets"),
  token: z.string().describe("The token symbol involved in this action"),
  description: z
    .string()
    .describe("Detailed explanation of what this action will do"),
  priority: z
    .enum(["low", "medium", "high", "critical"] as const)
    .describe("How urgent this action is")
    .optional(),
  params: z
    .record(z.union([z.string(), z.number(), z.boolean()]))
    .describe("Parameters needed for this action (amounts, destinations, etc.)")
    .optional(),
});

/**
 * Schema for the action recommendation result
 */
export const actionRecommendationSchema = z.object({
  actions: z
    .array(actionItemSchema)
    .describe("List of recommended actions to take"),
});

export type ActionItem = z.infer<typeof actionItemSchema>;
export type ActionRecommendationResult = z.infer<
  typeof actionRecommendationSchema
>;

// Export as default as well
export default actionRecommendationSchema;
