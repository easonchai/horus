import dependencyGraphData from "../data/dependency_graph.json";
import { DependencyGraph } from "../models/config";

// Types for the dependency graph entries
interface SwapFunction {
  protocol: string;
  contractType: string;
  functionName: string;
  arguments: Record<string, string>[];
  pairs: {
    to: string;
    fee: number;
  }[];
}

interface ExitFunction {
  contractType: string;
  functionName: string;
  arguments: Record<string, string>[];
}

interface UnderlyingToken {
  symbol: string;
  ratio: string;
}

export class DependencyGraphService {
  private static dependencyData = dependencyGraphData;
  private static protocolToDependenciesMap: DependencyGraph =
    DependencyGraphService.buildProtocolToDependenciesMap();
  private static tokenToProtocolsMap: Record<string, string[]> =
    DependencyGraphService.buildTokenToProtocolsMap();

  /**
   * Get the complete dependency graph mapping protocols to their dependencies
   */
  public static getDependencyGraph(): DependencyGraph {
    return DependencyGraphService.protocolToDependenciesMap;
  }

  /**
   * Get dependencies for a specific protocol
   */
  public static getDependenciesByProtocol(protocol: string): string[] {
    return DependencyGraphService.protocolToDependenciesMap[protocol] || [];
  }

  /**
   * Get protocols that a token is associated with
   */
  public static getProtocolsByToken(token: string): string[] {
    return DependencyGraphService.tokenToProtocolsMap[token] || [];
  }

  /**
   * Get swap functions for a specific token
   */
  public static getSwapFunctions(token: string): SwapFunction[] {
    const entry = DependencyGraphService.dependencyData.dependencies.find(
      (e) => e.derivativeSymbol === token
    );
    return entry?.swapFunctions || [];
  }

  /**
   * Get exit functions for a specific token
   */
  public static getExitFunctions(token: string): ExitFunction[] {
    const entry = DependencyGraphService.dependencyData.dependencies.find(
      (e) => e.derivativeSymbol === token
    );
    return entry?.exitFunctions || [];
  }

  /**
   * Get underlying tokens for a specific token
   */
  public static getUnderlyingTokens(
    token: string
  ): (string | UnderlyingToken)[] {
    const entry = DependencyGraphService.dependencyData.dependencies.find(
      (e) => e.derivativeSymbol === token
    );
    return entry?.underlyings || [];
  }

  /**
   * Get all tokens for a specific chain
   */
  public static getTokensByChain(chainId: string): string[] {
    return DependencyGraphService.dependencyData.dependencies
      .filter((entry) => entry.chainId === chainId)
      .map((entry) => entry.derivativeSymbol);
  }

  /**
   * Build the protocol to dependencies map
   */
  private static buildProtocolToDependenciesMap(): DependencyGraph {
    const map: DependencyGraph = {};

    DependencyGraphService.dependencyData.dependencies.forEach((entry) => {
      if (entry.protocol) {
        if (!map[entry.protocol]) {
          map[entry.protocol] = [];
        }
        map[entry.protocol].push(entry.derivativeSymbol);
      }

      // Also add swap function protocols
      entry.swapFunctions?.forEach((swapFunction) => {
        if (!map[swapFunction.protocol]) {
          map[swapFunction.protocol] = [];
        }
        if (!map[swapFunction.protocol].includes(entry.derivativeSymbol)) {
          map[swapFunction.protocol].push(entry.derivativeSymbol);
        }
      });
    });

    return map;
  }

  /**
   * Build the token to protocols map
   */
  private static buildTokenToProtocolsMap(): Record<string, string[]> {
    const map: Record<string, string[]> = {};

    DependencyGraphService.dependencyData.dependencies.forEach((entry) => {
      if (!map[entry.derivativeSymbol]) {
        map[entry.derivativeSymbol] = [];
      }

      if (
        entry.protocol &&
        !map[entry.derivativeSymbol].includes(entry.protocol)
      ) {
        map[entry.derivativeSymbol].push(entry.protocol);
      }

      // Also add swap function protocols
      entry.swapFunctions?.forEach((swapFunction) => {
        if (!map[entry.derivativeSymbol].includes(swapFunction.protocol)) {
          map[entry.derivativeSymbol].push(swapFunction.protocol);
        }
      });
    });

    return map;
  }
}
