/**
 * Formats a date string (YYYY-MM-DD) into a readable format (e.g., "20 Sep 2026").
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
export function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString + 'T00:00:00');
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });
}

/**
 * Formats a short date (e.g., "20 Sep").
 * @param {string} dateString - ISO date string
 * @returns {string} Short formatted date
 */
export function formatDateShort(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString + 'T00:00:00');
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short'
  });
}
