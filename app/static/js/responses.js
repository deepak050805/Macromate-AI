const unreadable = () => new Error("The server returned an unreadable response. Try again.");

function validDate(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00.000Z`);
  return Number.isFinite(parsed.getTime()) && parsed.getUTCFullYear() >= 1 &&
    parsed.toISOString().slice(0, 10) === value;
}

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
  if (record.date !== null && !validDate(record.date)) throw unreadable();
  return record;
}

export function validateProgressPage(data, requestedPage) {
  validatePage(data, requestedPage, data?.records, 20);
  for (const record of data.records) validateProgressRecord(record);
  return data;
}

export function validateSavedProgress(data, submitted, editing = "") {
  const record = validateProgressRecord(data?.record);
  if (
    (editing && record.id !== Number(editing)) ||
    record.date !== submitted.date || record.weight !== Number(submitted.weight) ||
    record.calories !== Number(submitted.calories)
  ) throw unreadable();
  return record;
}

export function validateProgressSummary(data, interval = null) {
  if (!data || typeof data !== "object" || Array.isArray(data) ||
    !Number.isSafeInteger(data.total) || data.total < 0 ||
    !Number.isSafeInteger(data.dated) || data.dated < 0 || data.dated > data.total)
    throw unreadable();
  for (const [field, maximum] of [["average_weight", 500], ["average_calories", 20000]]) {
    const value = data[field];
    if (data.total === 0 ? value !== null : !Number.isFinite(value) || value < 0 || value > maximum)
      throw unreadable();
  }
  if (data.dated === 0) {
    if (data.first_date !== null || data.last_date !== null) throw unreadable();
  } else if (!validDate(data.first_date) || !validDate(data.last_date) || data.first_date > data.last_date)
    throw unreadable();
  if (data.dated < 2 ? data.weight_change !== null :
    !Number.isFinite(data.weight_change) || Math.abs(data.weight_change) > 500)
    throw unreadable();
  if (interval && (interval.date_from || interval.date_to)) {
    if (data.dated !== data.total || (data.dated > 0 && (
      (interval.date_from && data.first_date < interval.date_from) ||
      (interval.date_to && data.last_date > interval.date_to)
    ))) throw unreadable();
  }
  return data;
}
