import protocolsData from "../data/protocols.json";
import { DependencyGraph } from "../models/config";

export class ProtocolService {
  /**
   * Returns protocol data from the JSON
   */
  public static getProtocolData() {
    return protocolsData.protocols;
  }

  /**
   * Builds a dependency graph from protocols.json
   */
  public static getDependencyGraph(): DependencyGraph {
    const graph: DependencyGraph = {};

    this.getProtocolData().forEach((protocol) => {
      // Get first available chain
      const chainIds = Object.keys(protocol.chains);
      if (chainIds.length > 0) {
        const chainId = chainIds[0];
        // Use type assertion to handle the dynamic access
        const contracts =
          protocol.chains[chainId as keyof typeof protocol.chains];

        // Use contract names as dependencies
        graph[protocol.name] = Object.keys(contracts);
      }
    });

    return graph;
  }

  /**
   * Normalizes protocol names to match exact case in protocols.json
   */
  public static getNormalizedProtocolName(name: string): string | undefined {
    // Create mapping on demand for case-insensitive lookups
    const protocolNameMap = new Map(
      this.getProtocolData().map((p) => [p.name.toLowerCase(), p.name])
    );

    return protocolNameMap.get(name.toLowerCase());
  }

  /**
   * Returns all protocol names from the configuration
   */
  public static getAllProtocolNames(): string[] {
    return this.getProtocolData().map((p) => p.name);
  }
}
