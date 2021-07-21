import { Tag } from 'interfaces';
import * as qs from 'simple-query-string';

export function sortTagsAlphabetical(a: Tag, b: Tag): number {
  return a.tag_name.localeCompare(b.tag_name);
}

export function extractFromObj(
  initialObj: object,
  desiredKeys: string[]
): object {
  return Object.keys(initialObj)
    .filter((key) => desiredKeys.indexOf(key) > -1)
    .reduce((obj, key) => {
      obj[key] = initialObj[key];
      return obj;
    }, {});
}

export function filterFromObj(
  initialObj: object,
  rejectedKeys: string[]
): object {
  return Object.keys(initialObj)
    .filter((key) => rejectedKeys.indexOf(key) === -1)
    .reduce((obj, key) => {
      obj[key] = initialObj[key];
      return obj;
    }, {});
}

/**
 * Takes a parameter objects and generates the query string parameters needed for requests.
 * Example:
 * const queryParameters = getQueryParams({key: tableData.key, column_name: columnName})
 */
export function getQueryParams(params: object): string {
  return qs.stringify(params);
}
