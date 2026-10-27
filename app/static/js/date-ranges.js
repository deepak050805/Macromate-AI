export function utcDateRange(days, now = new Date()) {
  if (!Number.isInteger(days) || days < 1 || days > 366 ||
    !(now instanceof Date) || !Number.isFinite(now.getTime()))
    throw new RangeError("Choose a valid date interval.");
  const dateTo = now.toISOString().slice(0, 10);
  if (dateTo < "2000-01-01") throw new RangeError("Supported dates start at 2000-01-01.");
  const end = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  const start = Math.max(Date.UTC(2000, 0, 1), end - (days - 1) * 86400000);
  return { date_from: new Date(start).toISOString().slice(0, 10), date_to: dateTo };
}
