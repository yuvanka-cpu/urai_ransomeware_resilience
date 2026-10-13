import { describe, expect, it } from 'vitest'
import { formatAttackRiskScore } from './ransomwareRiskScore'

describe('Attack Risk Score formatting', () => {
  it('formats calibrated probability on a 0–100 scale', () => {
    expect(formatAttackRiskScore(0.43)).toBe('43.0/100')
    expect(formatAttackRiskScore(0)).toBe('0.0/100')
    expect(formatAttackRiskScore(1)).toBe('100.0/100')
  })

  it('rejects missing probabilities', () => {
    expect(formatAttackRiskScore(undefined)).toBe('Unavailable')
    expect(formatAttackRiskScore(null)).toBe('Unavailable')
  })

  it('rejects invalid probabilities', () => {
    expect(formatAttackRiskScore(-0.1)).toBe('Unavailable')
    expect(formatAttackRiskScore(1.1)).toBe('Unavailable')
    expect(formatAttackRiskScore(NaN)).toBe('Unavailable')
    expect(formatAttackRiskScore(Infinity)).toBe('Unavailable')
  })
})
