import { describe, expect, it } from 'vitest';
import {
  formatKopecks,
  kopecksToInput,
  parseRublesToKopecks,
  lessonPlural,
} from './pricing';

describe('lesson price formatting', () => {
  it('parses rubles and kopecks exactly, including zero and blank', () => {
    expect(parseRublesToKopecks('800')).toBe(80_000);
    expect(parseRublesToKopecks('800,5')).toBe(80_050);
    expect(parseRublesToKopecks('800.05')).toBe(80_005);
    expect(parseRublesToKopecks('0')).toBe(0);
    expect(parseRublesToKopecks('  ')).toBeNull();
  });

  it('rejects ambiguous precision and values outside the API range', () => {
    expect(() => parseRublesToKopecks('1,001')).toThrow();
    expect(() => parseRublesToKopecks('-1')).toThrow();
    expect(() => parseRublesToKopecks('21474836,48')).toThrow();
    expect(parseRublesToKopecks('21474836,47')).toBe(2_147_483_647);
  });

  it('formats exact kopecks and distinguishes an unknown price from zero', () => {
    expect(formatKopecks(160_005)).toBe('1 600,05 ₽');
    expect(formatKopecks(0)).toBe('0,00 ₽');
    expect(kopecksToInput(null)).toBe('');
    expect(kopecksToInput(0)).toBe('0,00');
    expect(lessonPlural(1)).toBe('занятие');
    expect(lessonPlural(4)).toBe('занятия');
    expect(lessonPlural(5)).toBe('занятий');
  });
});
