export interface DependencyGraph {
  [protocol: string]: string[];
}

export interface Protocol {
  id: string;
  name: string;
  contracts: {
    [chainId: string]: string;
  };
}

export interface Token {
  symbol: string;
  name: string;
  decimals: number;
  addresses: {
    [chainId: string]: string;
  };
}
