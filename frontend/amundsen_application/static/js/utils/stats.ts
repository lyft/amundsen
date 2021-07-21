import { formatDate } from 'utils/dateUtils';

import { getUniqueValueStatTypeName } from 'config/config-utils';

import { ColumnUniqueValues, TableColumnStats } from 'interfaces/index';

const mapIntoUniqueValueFormat = ([k, v]): ColumnUniqueValues => ({
  value: k,
  count: v,
});
const parseRawUniqueValues = (uniqueValues: string) => {
  let parsedUniqueValues = {};

  try {
    parsedUniqueValues = JSON.parse(uniqueValues.split("'").join('"'));
  } catch (e) {
    // eslint-disable-next-line no-console
    console.log('Error parsing unique values on stats!');
  }

  return parsedUniqueValues;
};

/**
 * Parses the stats' unique values key into an array of
 * objects with value and count properties
 * @param statsList
 * @returns ColumnUniqueValues[]
 */
export const getUniqueValues = (
  statsList: TableColumnStats[]
): ColumnUniqueValues[] | [] => {
  const uniqueValuesKey = getUniqueValueStatTypeName();
  if (!uniqueValuesKey) {
    return [];
  }

  const uniqueValues = statsList.find(
    (item) => item.stat_type === uniqueValuesKey
  );

  if (uniqueValues) {
    return Object.entries(parseRawUniqueValues(uniqueValues.stat_val)).map(
      mapIntoUniqueValueFormat
    );
  }

  return [];
};

/**
 * Removes any stat identified as a unique value
 * @param statsList
 * @returns TableColumnStats[]
 */
export const filterOutUniqueValues = (statsList: TableColumnStats[]) => {
  const uniqueValuesKey = getUniqueValueStatTypeName();

  return statsList.filter((item) => item.stat_type !== uniqueValuesKey);
};

/**
 * Creates the stats info message from the start and end epoch timestamps
 * @param startEpoch
 * @param endEpoch
 * @returns string
 */
export const getStatsInfoText = (startEpoch?: number, endEpoch?: number) => {
  const startDate = startEpoch
    ? formatDate({ epochTimestamp: startEpoch })
    : null;
  const endDate = endEpoch ? formatDate({ epochTimestamp: endEpoch }) : null;

  let infoText = 'Stats reflect data collected';

  if (startDate && endDate) {
    if (startDate === endDate) {
      infoText = `${infoText} on ${startDate} only. (daily partition)`;
    } else {
      infoText = `${infoText} between ${startDate} and ${endDate}.`;
    }
  } else {
    infoText = `${infoText} over a recent period of time.`;
  }

  return infoText;
};
