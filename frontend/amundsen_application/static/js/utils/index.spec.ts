import { API_PATH } from 'ducks/tableMetadata/api/v0';
import { ResourceType } from 'interfaces/Resources';
import { UpdateMethod } from 'interfaces/Enums';

import * as DateUtils from './dateUtils';
import * as LogUtils from './logUtils';
import * as NavigationUtils from './navigationUtils';
import * as NumberUtils from './numberUtils';
import * as TextUtils from './textUtils';
import * as OwnerUtils from './ownerUtils';
import * as StatUtils from './stats';

jest.mock('config/config-utils', () => ({
  getUniqueValueStatTypeName: jest.fn(() => 'distinctValues'),
  getNumberFormat: jest.fn(() => null),
}));

describe('textUtils', () => {
  describe('convertText', () => {
    it('converts to lower case', () => {
      const actual = TextUtils.convertText(
        'TESt LoWer cASe',
        TextUtils.CaseType.LOWER_CASE
      );
      const expected = 'test lower case';

      expect(actual).toEqual(expected);
    });

    it('converts to sentence case', () => {
      const actual = TextUtils.convertText(
        'tESt sentence cASe',
        TextUtils.CaseType.SENTENCE_CASE
      );
      const expected = 'Test sentence case';

      expect(actual).toEqual(expected);
    });

    it('converts to upper case', () => {
      const actual = TextUtils.convertText(
        'test upper cASe',
        TextUtils.CaseType.UPPER_CASE
      );
      const expected = 'TEST UPPER CASE';

      expect(actual).toEqual(expected);
    });

    it('converts to title case', () => {
      const actual = TextUtils.convertText(
        'tEST title cASe',
        TextUtils.CaseType.TITLE_CASE
      );
      const expected = 'Test Title Case';

      expect(actual).toEqual(expected);
    });
  });
});

describe('numberUtils', () => {
  describe('isNumber', () => {
    it('returns true if string is number', () => {
      const actual = NumberUtils.isNumber('1234');
      const expected = true;

      expect(actual).toEqual(expected);
    });
    it('returns false if string is not number', () => {
      const actualString = NumberUtils.isNumber('abcd');
      const actualDate = NumberUtils.isNumber('2020-11-03');
      const actualAlphaNum = NumberUtils.isNumber('1a2b3c');
      const expected = false;

      expect(actualString).toEqual(expected);
      expect(actualDate).toEqual(expected);
      expect(actualAlphaNum).toEqual(expected);
    });
  });
  describe('formatNumber', () => {
    it('returns formatted number', () => {
      const actual = NumberUtils.formatNumber('1998');
      const expected = '1,998';

      expect(actual).toEqual(expected);
    });
    it('get NaN on non numbers', () => {
      const actual = NumberUtils.formatNumber('2020-11-03');
      const expected = 'NaN';

      expect(actual).toEqual(expected);
    });
  });
});

describe('navigationUtils', () => {
  describe('updateSearchUrl', () => {
    let mockUrl;
    let generateSearchUrlSpy;
    let historyReplaceSpy;
    let historyPushSpy;
    let searchParams;

    beforeAll(() => {
      mockUrl = 'testUrl';
      generateSearchUrlSpy = jest
        .spyOn(NavigationUtils, 'generateSearchUrl')
        .mockReturnValue(mockUrl);
      historyReplaceSpy = jest.spyOn(NavigationUtils.BrowserHistory, 'replace');
      historyPushSpy = jest.spyOn(NavigationUtils.BrowserHistory, 'push');
      searchParams = {
        term: 'test',
        resource: ResourceType.table,
        index: 0,
      };
    });

    it('calls history.replace when replace is true', () => {
      historyReplaceSpy.mockClear();
      historyPushSpy.mockClear();
      NavigationUtils.updateSearchUrl(searchParams, true);

      expect(historyReplaceSpy).toHaveBeenCalledWith(mockUrl);
      expect(historyPushSpy).not.toHaveBeenCalled();
    });

    it('calls history.push when replace is false', () => {
      historyReplaceSpy.mockClear();
      historyPushSpy.mockClear();
      NavigationUtils.updateSearchUrl(searchParams, false);

      expect(historyReplaceSpy).not.toHaveBeenCalled();
      expect(historyPushSpy).toHaveBeenCalledWith(mockUrl);
    });

    it('calls history.push when default replace value is used', () => {
      historyReplaceSpy.mockClear();
      historyPushSpy.mockClear();
      NavigationUtils.updateSearchUrl(searchParams);

      expect(historyReplaceSpy).not.toHaveBeenCalled();
      expect(historyPushSpy).toHaveBeenCalledWith(mockUrl);
    });

    it('calls generateSearchUrl with searchParams', () => {
      generateSearchUrlSpy.mockClear();
      NavigationUtils.updateSearchUrl(searchParams, true);

      expect(generateSearchUrlSpy).toHaveBeenCalledTimes(1);
      expect(generateSearchUrlSpy).toHaveBeenCalledWith(searchParams);
    });

    afterAll(() => {
      generateSearchUrlSpy.mockRestore();
    });
  });

  describe('generaSearchUrl', () => {
    let testResource;
    let searchParams;
    let url;

    it('returns default route if falsy search term and no filters', () => {
      searchParams = {
        term: '',
        resource: ResourceType.table,
        index: 0,
      };
      url = NavigationUtils.generateSearchUrl(searchParams);
      expect(url).toBe(NavigationUtils.DEFAULT_SEARCH_ROUTE);
    });

    it('excludes term from the url if term is falsy', () => {
      testResource = ResourceType.table;
      searchParams = {
        term: '',
        resource: testResource,
        index: 0,
        filters: {
          [testResource]: { column: 'column_name' },
        },
      };
      url = NavigationUtils.generateSearchUrl(searchParams);
      expect(url.includes('term=')).toBe(false);
    });

    it('excludes filters from the url if no filters', () => {
      searchParams = {
        term: 'test',
        resource: ResourceType.table,
        index: 0,
      };
      url = NavigationUtils.generateSearchUrl(searchParams);
      expect(url.includes('filters=')).toBe(false);
    });

    it('generates expected url for all valid searchParams', () => {
      const testTerm = 'test';
      const testIndex = 0;
      testResource = ResourceType.table;
      searchParams = {
        term: testTerm,
        resource: testResource,
        index: 0,
        filters: {
          [testResource]: { column: 'column_name' },
        },
      };
      url = NavigationUtils.generateSearchUrl(searchParams);
      const expectedFilterString = `%7B%22column%22%3A%22column_name%22%7D`;
      const expectedUrl = `/search?term=${testTerm}&resource=${testResource}&index=${testIndex}&filters=${expectedFilterString}`;
      expect(url).toEqual(expectedUrl);
    });
  });

  describe('buildDashboardURL', () => {
    it('encodes the passed URI for safe use on the URL bar', () => {
      const testURI = 'product_dashboard://cluster.groupID/dashboardID';
      const expected =
        '/dashboard/product_dashboard%3A%2F%2Fcluster.groupID%2FdashboardID';
      const actual = NavigationUtils.buildDashboardURL(testURI);

      expect(actual).toEqual(expected);
    });
  });

  describe('buildLineageURL', () => {
    it('builds a path to the lineage page from table metadata', () => {
      const mockMetadata = {
        cluster: 'cluster',
        database: 'database',
        schema: 'schema',
        name: 'name',
      };
      const expected = `/lineage/table/cluster/database/schema/name`;
      const actual = NavigationUtils.buildLineageURL(mockMetadata);

      expect(actual).toEqual(expected);
    });
  });

  describe('buildTableKey', () => {
    it('picks up url params and constructs a table key for backed interactions', () => {
      const testMatch = {
        cluster: 'cluster',
        database: 'database',
        schema: 'schema',
        table: 'table',
      };
      const expected = 'database://cluster.schema/table';
      const actual = NavigationUtils.buildTableKey(testMatch);

      expect(actual).toEqual(expected);
    });
  });
});

describe('dateUtils', () => {
  describe('getMomentDate', () => {
    it('parses a timestamp', () => {
      const config = { timestamp: 1580421964000 };
      const moment = DateUtils.getMomentDate(config);
      const dateString = moment.format('MMM DD, YYYY');
      expect(dateString).toEqual('Jan 30, 2020');
    });

    it('parses an epoch timestamp', () => {
      const config = { epochTimestamp: 1580421964 };
      const moment = DateUtils.getMomentDate(config);
      const dateString = moment.format('MMM DD, YYYY');
      expect(dateString).toEqual('Jan 30, 2020');
    });

    it('parses an date string', () => {
      const config = {
        dateString: '2020-Jan-30',
        dateStringFormat: 'YYYY-MMM-DD',
      };
      const moment = DateUtils.getMomentDate(config);
      const dateString = moment.format('MMM DD, YYYY');
      expect(dateString).toEqual('Jan 30, 2020');
    });
  });

  describe('formatDate', () => {
    it('formats a date to the default format', () => {
      const config = { timestamp: 1580421964000 };
      const dateString = DateUtils.formatDate(config);
      expect(dateString).toEqual('Jan 30, 2020');
    });
  });

  describe('formatDateTimeShort', () => {
    it('formats a date to the date time short format', () => {
      const config = { timestamp: 1580421964000 };
      const dateString = DateUtils.formatDateTimeShort(config);
      // This test may fail in your IDE if your timezone is not set to GMT
      expect(dateString).toEqual('Jan 30, 2020 10pm GMT');
    });
  });

  describe('formatDateTimeLong', () => {
    const config = { timestamp: 1580421964000 };
    const dateString = DateUtils.formatDateTimeLong(config);
    expect(dateString).toEqual('January 30th 2020 at 10:06:04 pm');
  });
});

describe('logUtils', () => {
  describe('getLoggingParams', () => {
    let searchString;
    let replaceStateSpy;

    beforeAll(() => {
      replaceStateSpy = jest.spyOn(window.history, 'replaceState');
    });

    it('returns the parsed source and index in an object', () => {
      searchString = 'source=test_source&index=10';
      const params = LogUtils.getLoggingParams(searchString);
      expect(params.source).toEqual('test_source');
      expect(params.index).toEqual('10');
    });

    it('clears the logging params from the URL, if present', () => {
      const uri = 'testUri';
      const mockFilter = '{"tag":"tagName"}';
      searchString = `uri=${uri}&filters=${mockFilter}&source=test_source&index=10`;
      replaceStateSpy.mockClear();
      LogUtils.getLoggingParams(searchString);
      expect(replaceStateSpy).toHaveBeenCalledWith(
        {},
        '',
        `${window.location.origin}${window.location.pathname}?uri=${uri}&filters=${mockFilter}`
      );
    });

    it('does not clear the logging params if they do not exist', () => {
      searchString = '';
      replaceStateSpy.mockClear();
      LogUtils.getLoggingParams(searchString);
      expect(replaceStateSpy).not.toHaveBeenCalled();
    });
  });
});

describe('stats utils', () => {
  const STATS_WITH_NO_UNIQUE_VALUES = [
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'count_null',
      stat_val: '48.0',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'count_zero',
      stat_val: '0.0',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'approx_distinct_count',
      stat_val: '5.0',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'stddev_value',
      stat_val: '1.1710452355200918',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'median_value',
      stat_val: '4.0',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'min_value',
      stat_val: '4.0',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'avg_value',
      stat_val: '4.622641509433962',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'max_value',
      stat_val: '7.0',
    },
    {
      end_epoch: 1615593600,
      start_epoch: 1613001600,
      stat_type: 'column_usage',
      stat_val: '70',
    },
  ];
  const STATS_WITH_SIX_UNIQUE_VALUES = [
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'count_null',
      stat_val: '48.0',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'count_zero',
      stat_val: '0.0',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'approx_distinct_count',
      stat_val: '5.0',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'stddev_value',
      stat_val: '1.1710452355200918',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'median_value',
      stat_val: '4.0',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'min_value',
      stat_val: '4.0',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'avg_value',
      stat_val: '4.622641509433962',
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'distinctValues',
      stat_val:
        "{'lyft': 162, 'grab': 66, 'unknown': 54, 'null': 48, 'unkown': 18, 'didi': 18}",
    },
    {
      end_epoch: 1609522182,
      start_epoch: 1608917382,
      stat_type: 'max_value',
      stat_val: '7.0',
    },
    {
      end_epoch: 1615593600,
      start_epoch: 1613001600,
      stat_type: 'column_usage',
      stat_val: '70',
    },
  ];
  const STRINGIFIED_ARRAY_UNIQUE_VALUES = [
    {
      end_epoch: 1617147150,
      start_epoch: 1616542350,
      stat_type: 'count_null',
      stat_val: '0.0',
    },
    {
      end_epoch: 1617147150,
      start_epoch: 1616542350,
      stat_type: 'count_zero',
      stat_val: '4378016.0',
    },
    {
      end_epoch: 1617147150,
      start_epoch: 1616542350,
      stat_type: 'stddev_value',
      stat_val: '0.5856386084183235',
    },
    {
      end_epoch: 1617147150,
      start_epoch: 1616542350,
      stat_type: 'avg_value',
      stat_val: '0.6695026231618191',
    },
    {
      end_epoch: 1617147150,
      start_epoch: 1616542350,
      stat_type: 'distinctValues',
      stat_val:
        '{1: 5756008, 0: 4450396, 2: 591892, 3: 12948, 4: 424, 5: 40, 11: 16, 7: 12, 6: 8, 9: 8, 8: 4, 10: 4}',
    },
    {
      end_epoch: 1617147150,
      start_epoch: 1616542350,
      stat_type: 'approx_distinct_count',
      stat_val: '13.0',
    },
    {
      end_epoch: 1617147150,
      start_epoch: 1616542350,
      stat_type: 'max_value',
      stat_val: '12.0',
    },
    {
      end_epoch: 1617147150,
      start_epoch: 1616542350,
      stat_type: 'min_value',
      stat_val: '0.0',
    },
    {
      end_epoch: 1617147150,
      start_epoch: 1616542350,
      stat_type: 'median_value',
      stat_val: '0.9907752863495858',
    },
    {
      end_epoch: 1615593600,
      start_epoch: 1613001600,
      stat_type: 'column_usage',
      stat_val: '78',
    },
  ];

  describe('getUniqueValues', () => {
    it('returns an empty array when there is no stats', () => {
      const expected = 0;
      const actual = StatUtils.getUniqueValues([]).length;

      expect(actual).toEqual(expected);
    });

    it('returns an empty array when there is no unique values in the stats', () => {
      const expected = 0;
      const actual = StatUtils.getUniqueValues(STATS_WITH_NO_UNIQUE_VALUES)
        .length;

      expect(actual).toEqual(expected);
    });

    describe('when there is one unique value in the stats', () => {
      const STATS_WITH_ONE_UNIQUE_VALUE = [
        {
          end_epoch: 1609522182,
          start_epoch: 1608917382,
          stat_type: 'count_null',
          stat_val: '48.0',
        },
        {
          end_epoch: 1609522182,
          start_epoch: 1608917382,
          stat_type: 'count_zero',
          stat_val: '0.0',
        },
        {
          end_epoch: 1609522182,
          start_epoch: 1608917382,
          stat_type: 'approx_distinct_count',
          stat_val: '5.0',
        },
        {
          end_epoch: 1609522182,
          start_epoch: 1608917382,
          stat_type: 'stddev_value',
          stat_val: '1.1710452355200918',
        },
        {
          end_epoch: 1609522182,
          start_epoch: 1608917382,
          stat_type: 'median_value',
          stat_val: '4.0',
        },
        {
          end_epoch: 1609522182,
          start_epoch: 1608917382,
          stat_type: 'min_value',
          stat_val: '4.0',
        },
        {
          end_epoch: 1609522182,
          start_epoch: 1608917382,
          stat_type: 'avg_value',
          stat_val: '4.622641509433962',
        },
        {
          end_epoch: 1609522182,
          start_epoch: 1608917382,
          stat_type: 'distinctValues',
          stat_val: "{'lyft': 162}",
        },
        {
          end_epoch: 1609522182,
          start_epoch: 1608917382,
          stat_type: 'max_value',
          stat_val: '7.0',
        },
        {
          end_epoch: 1615593600,
          start_epoch: 1613001600,
          stat_type: 'column_usage',
          stat_val: '70',
        },
      ];

      it('returns an array with one element', () => {
        const expected = 1;
        const actual = StatUtils.getUniqueValues(STATS_WITH_ONE_UNIQUE_VALUE)
          .length;

        expect(actual).toEqual(expected);
      });

      it('returns an array with one element with a value and count', () => {
        const expectedValue = 'string';
        const actualValue = typeof StatUtils.getUniqueValues(
          STATS_WITH_ONE_UNIQUE_VALUE
        )[0].value;
        const expectedCount = 'number';
        const actualCount = typeof StatUtils.getUniqueValues(
          STATS_WITH_ONE_UNIQUE_VALUE
        )[0].count;

        expect(actualValue).toEqual(expectedValue);
        expect(actualCount).toEqual(expectedCount);
      });
    });

    describe('when there are six unique value in the stats', () => {
      it('returns an array with six elements', () => {
        const expected = 6;
        const actual = StatUtils.getUniqueValues(STATS_WITH_SIX_UNIQUE_VALUES)
          .length;

        expect(actual).toEqual(expected);
      });
    });

    describe('when there are unique values as a stringified array', () => {
      it('returns an array with zero elements', () => {
        const expected = 0;
        const actual = StatUtils.getUniqueValues(
          STRINGIFIED_ARRAY_UNIQUE_VALUES
        ).length;

        expect(actual).toEqual(expected);
      });
    });
  });

  describe('filterOutUniqueValues', () => {
    describe('when there is no unique values', () => {
      it('returns the same stat object', () => {
        const expected = STATS_WITH_NO_UNIQUE_VALUES;
        const actual = StatUtils.filterOutUniqueValues(
          STATS_WITH_NO_UNIQUE_VALUES
        );

        expect(actual).toEqual(expected);
      });
    });

    describe('when there are unique values', () => {
      it('returns an object with no unique values', () => {
        const expected = STATS_WITH_NO_UNIQUE_VALUES;
        const actual = StatUtils.filterOutUniqueValues(
          STATS_WITH_SIX_UNIQUE_VALUES
        );

        expect(actual).toEqual(expected);
      });
    });
  });

  describe('getStatsInfoText', () => {
    it('generates correct info text for a daily partition', () => {
      const startEpoch = 1568160000;
      const endEpoch = 1568160000;
      const expected = `Stats reflect data collected on Sep 11, 2019 only. (daily partition)`;
      const actual = StatUtils.getStatsInfoText(startEpoch, endEpoch);

      expect(actual).toEqual(expected);
    });

    it('generates correct info text for a date range', () => {
      const startEpoch = 1568160000;
      const endEpoch = 1571616000;
      const expected = `Stats reflect data collected between Sep 11, 2019 and Oct 21, 2019.`;
      const actual = StatUtils.getStatsInfoText(startEpoch, endEpoch);

      expect(actual).toEqual(expected);
    });

    it('generates correct when no dates are given', () => {
      const expected = `Stats reflect data collected over a recent period of time.`;
      const actual = StatUtils.getStatsInfoText();

      expect(actual).toEqual(expected);
    });
  });
});

describe('ownerUtils', () => {
  describe('createOwnerUpdatePayload', () => {
    it('creates the right update payload', () => {
      const testId = 'testId@test.com';
      const testKey = 'testKey';
      const testMethod = UpdateMethod.PUT;
      expect(
        OwnerUtils.createOwnerUpdatePayload(ResourceType.table, testKey, {
          method: testMethod,
          id: testId,
        })
      ).toMatchObject({
        method: testMethod,
        url: `${API_PATH}/update_table_owner`,
        data: {
          key: testKey,
          owner: testId,
        },
      });
    });
  });

  describe('getOwnersDictFromUsers ', () => {
    it('correctly reformats users into the owners dict', () => {
      const mockUsers = [
        {
          display_name: 'test',
          profile_url: 'test.io',
          email: 'test@test.com',
          user_id: 'test',
        },
      ];
      expect(OwnerUtils.getOwnersDictFromUsers(mockUsers)).toEqual({
        test: {
          display_name: 'test',
          profile_url: 'test.io',
          email: 'test@test.com',
          user_id: 'test',
        },
      });
    });
  });
  describe('createOwnerUpdatePayload ', () => {
    it('correctly reformats users into the owners dict', () => {
      const mockResourceType = ResourceType.table;
      const mockKey = 'testKey';
      const mockPayload = {
        id: 'testId',
        method: UpdateMethod.PUT,
      };
      expect(
        OwnerUtils.createOwnerUpdatePayload(
          mockResourceType,
          mockKey,
          mockPayload
        )
      ).toEqual({
        url: `${API_PATH}/update_table_owner`,
        method: mockPayload.method,
        data: {
          key: mockKey,
          owner: mockPayload.id,
        },
      });
    });
  });
});
