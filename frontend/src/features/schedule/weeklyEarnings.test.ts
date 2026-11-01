import { describe, expect, it } from 'vitest';
import { weeklyEarningsSummary } from './WeeklyEarnings';

describe('weekly earnings summary', () => {
  it('labels a complete total plainly, including an explicit zero', () => {
    expect(
      weeklyEarningsSummary({
        week: '2026-10-19',
        total_kopecks: 0,
        lesson_count: 2,
        completed_count: 0,
        unpriced_count: 0,
      }),
    ).toEqual({
      amountLabel: 'Итого',
      amount: '0,00 ₽',
      lessonCount: 2,
      completedCount: 0,
      incompleteMessage: null,
    });
  });

  it('labels a partial sum as known and identifies lessons without a price', () => {
    expect(
      weeklyEarningsSummary({
        week: '2026-10-19',
        total_kopecks: 80_000,
        lesson_count: 5,
        completed_count: 3,
        unpriced_count: 2,
      }),
    ).toEqual({
      amountLabel: 'Известная сумма',
      amount: '800,00 ₽',
      lessonCount: 5,
      completedCount: 3,
      incompleteMessage: 'Итог неполный: 2 занятия без указанной цены.',
    });
  });
});
