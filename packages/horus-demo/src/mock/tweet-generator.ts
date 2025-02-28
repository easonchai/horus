import { Signal } from '../models/types';

const securityAlerts = [
  'URGENT: Security vulnerability found in Uniswap V3 smart contract. Users advised to withdraw immediately.',
  'Breaking: Aave protocol pausing withdrawals due to suspicious activity.',
  'Alert: Potential exploit discovered in Curve Finance. Investigating.',
  'False alarm: Previous reports about Uniswap were incorrect. No action needed.',
  'Security Advisory: New phishing attacks targeting DeFi users. Be vigilant.'
];

export function generateRandomTweet(): Signal {
  const randomIndex = Math.floor(Math.random() * securityAlerts.length);
  return {
    id: `tweet-${Date.now()}`,
    source: 'twitter',
    content: securityAlerts[randomIndex],
    timestamp: Date.now()
  };
}
