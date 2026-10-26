const unreadable = () => new Error("The server returned an unreadable response. Try again.");

export function validatePage(data, requestedPage, items, pageSize) {
  if (
    data === null || typeof data !== "object" || Array.isArray(data) ||
    !Number.isSafeInteger(data.page) || data.page < 1 || data.page > 10000 ||
    data.page !== requestedPage ||
    !Number.isSafeInteger(data.pages) || data.pages < 0 ||
    !Number.isSafeInteger(data.total) || data.total < 0 ||
    !Array.isArray(items) || items.length > pageSize
  ) throw unreadable();
  return data;
}

export function validateProgressRecord(record) {
  if (
    record === null || typeof record !== "object" || Array.isArray(record) ||
    !Number.isSafeInteger(record.id) || record.id < 1 ||
    !Number.isFinite(record.weight) || record.weight <= 0 || record.weight > 500 ||
    !Number.isInteger(record.calories) || record.calories < 0 || record.calories > 20000
  ) throw unreadable();
  if (record.date !== null) {
    if (typeof record.date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(record.date))
      throw unreadable();
    const parsed = new Date(`${record.date}T00:00:00.000Z`);
    if (!Number.isFinite(parsed.getTime()) || parsed.getUTCFullYear() < 1 ||
      parsed.toISOString().slice(0, 10) !== record.date)
      throw unreadable();
  }
  return record;
}

export function validateProgressPage(data, requestedPage) {
  validatePage(data, requestedPage, data?.records, 20);
  for (const record of data.records) validateProgressRecord(record);
  return data;
}
