const MAX_PRICE_KOPECKS = 2_147_483_647;

/** Parses a plain ruble amount without converting through floating point. */
export function parseRublesToKopecks(input: string): number | null {
  const value = input.trim();
  if (!value) return null;

  const match = /^(\d+)(?:[,.](\d{1,2}))?$/.exec(value);
  if (!match) {
    throw new Error('Введите сумму в рублях, например 800 или 800,50');
  }

  const rubles = BigInt(match[1]);
  const kopecks = BigInt((match[2] || '').padEnd(2, '0') || '0');
  const amount = rubles * 100n + kopecks;
  if (amount > BigInt(MAX_PRICE_KOPECKS)) {
    throw new Error('Максимальная цена — 21 474 836,47 ₽');
  }
  return Number(amount);
}

function integerRubles(value: number) {
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(
    Math.floor(value / 100),
  );
}

export function formatKopecks(kopecks: number): string {
  const rubles = integerRubles(kopecks);
  const fractional = String(kopecks % 100).padStart(2, '0');
  return `${rubles},${fractional} ₽`;
}

export function kopecksToInput(kopecks: number | null): string {
  if (kopecks === null) return '';
  return `${Math.floor(kopecks / 100)},${String(kopecks % 100).padStart(2, '0')}`;
}

export function lessonPlural(count: number): string {
  const category = new Intl.PluralRules('ru-RU').select(count);
  const words: Record<string, string> = {
    one: 'занятие',
    few: 'занятия',
    many: 'занятий',
    other: 'занятия',
  };
  return words[category] ?? words.other;
}
