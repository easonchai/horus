import { describe, expect, it } from "vitest";
import { ThreatAnalysisResult, threatAnalysisSchema } from "../src/schemas";

describe("Schema Validation", () => {
  describe("Threat Analysis Schema", () => {
    it("should validate a correct threat analysis result", () => {
      const validThreatAnalysis: ThreatAnalysisResult = {
        isThreat: true,
        threatDetails: {
          description: "Critical vulnerability found in Uniswap V3 contracts",
          affectedProtocols: ["uniswap"],
          affectedTokens: ["ETH", "USDC"],
          chain: "ethereum",
          severity: "high",
        },
        analysisReasoning:
          "Based on the signal content, this appears to be a legitimate security concern",
      };

      const result = threatAnalysisSchema.safeParse(validThreatAnalysis);
      expect(result.success).toBe(true);
    });

    it("should validate when no threat is detected", () => {
      const noThreatAnalysis: ThreatAnalysisResult = {
        isThreat: false,
        analysisReasoning:
          "The tweet does not indicate any security vulnerability",
      };

      const result = threatAnalysisSchema.safeParse(noThreatAnalysis);
      expect(result.success).toBe(true);
    });

    it("should fail validation when threat is true but no threat details provided", () => {
      const invalidThreatAnalysis = {
        isThreat: true,
        // Missing threatDetails
        analysisReasoning: "This should fail validation",
      };

      const result = threatAnalysisSchema.safeParse(invalidThreatAnalysis);
      expect(result.success).toBe(false);
    });

    it("should fail validation with invalid severity level", () => {
      const invalidSeverityThreatAnalysis = {
        isThreat: true,
        threatDetails: {
          description: "Some description",
          affectedProtocols: ["uniswap"],
          affectedTokens: ["ETH"],
          chain: "ethereum",
          severity: "ultra-high", // Invalid severity level
        },
      };

      const result = threatAnalysisSchema.safeParse(
        invalidSeverityThreatAnalysis
      );
      expect(result.success).toBe(false);
    });

    it("should validate when using all valid severity levels", () => {
      const validSeverityLevels = [
        "low",
        "medium",
        "high",
        "critical",
      ] as const;

      validSeverityLevels.forEach((severity) => {
        const analysis: ThreatAnalysisResult = {
          isThreat: true,
          threatDetails: {
            description: "Test description",
            affectedProtocols: ["uniswap"],
            affectedTokens: ["ETH"],
            chain: "ethereum",
            severity,
          },
        };

        const result = threatAnalysisSchema.safeParse(analysis);
        expect(result.success).toBe(true);
      });
    });
  });
});
