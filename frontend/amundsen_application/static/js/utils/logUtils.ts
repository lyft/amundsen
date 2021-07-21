import * as qs from 'simple-query-string';

export function getLoggingParams(
  search: string
): { index: string; source: string } {
  const params = qs.parse(search);
  const { index } = params;
  const { source } = params;

  let queryString = '';
  let isInitialParam = true;
  Object.keys(params).forEach((key) => {
    if (key !== 'index' && key !== 'source') {
      queryString = isInitialParam
        ? `?${key}=${params[key]}`
        : `${queryString}&${key}=${params[key]}`;
      isInitialParam = false;
    }
  });

  // Remove logging params from URL
  if (source !== undefined || index !== undefined) {
    window.history.replaceState(
      {},
      '',
      `${window.location.origin}${window.location.pathname}${queryString}`
    );
  }
  return { index, source };
}
