import protocolsData from "../data/protocols.json";

export class ProtocolService {
  /**
   * Returns protocol data from the JSON
   */
  public static getProtocolData() {
    return protocolsData.protocols;
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
