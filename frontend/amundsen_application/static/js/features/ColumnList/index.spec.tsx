// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount } from 'enzyme';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { mocked } from 'ts-jest/utils';

import { SortDirection } from 'interfaces';
import { BadgeStyle } from 'config/config-types';
import * as ConfigUtils from 'config/config-utils';

import globalState from 'fixtures/globalState';
import ColumnList, { ColumnListProps } from '.';
import ColumnType from './ColumnType';
import { EMPTY_MESSAGE } from './constants';

import TestDataBuilder from './testDataBuilder';

jest.mock('config/config-utils');

const mockedNotificationsEnabled = mocked(
  ConfigUtils.notificationsEnabled,
  true
);
const mockedGetTableSortCriterias = mocked(
  ConfigUtils.getTableSortCriterias,
  true
);
const dataBuilder = new TestDataBuilder();
const middlewares = [];
const mockStore = configureStore(middlewares);

const setup = (propOverrides?: Partial<ColumnListProps>) => {
  const props = {
    editText: 'Click to edit description in the data source site',
    editUrl: 'https://test.datasource.site/table',
    database: 'testDatabase',
    columns: [],
    tableKey: 'test-key',
    openRequestDescriptionDialog: jest.fn(),
    ...propOverrides,
  };
  // Update state
  const testState = globalState;
  testState.tableMetadata.tableData.columns = props.columns;

  const wrapper = mount<ColumnListProps>(
    <Provider store={mockStore(testState)}>
      <ColumnList {...props} />
    </Provider>
  );

  return { props, wrapper };
};

describe('ColumnList', () => {
  mockedGetTableSortCriterias.mockReturnValue({
    sort_order: {
      name: 'Table Default',
      key: 'sort_order',
      direction: SortDirection.ascending,
    },
    usage: {
      name: 'Usage Count',
      key: 'usage',
      direction: SortDirection.descending,
    },
  });
  mockedNotificationsEnabled.mockReturnValue(true);

  describe('render', () => {
    it('renders without issues', () => {
      expect(() => {
        setup();
      }).not.toThrow();
    });

    describe('when empty columns are passed', () => {
      const { columns } = dataBuilder.withEmptyColumns().build();

      it('should render the custom empty messagee', () => {
        const { wrapper } = setup({ columns });
        const expected = EMPTY_MESSAGE;
        const actual = wrapper
          .find('.table-detail-table .ams-empty-message-cell')
          .text();

        expect(actual).toEqual(expected);
      });
    });

    describe('when simple type columns are passed', () => {
      const { columns } = dataBuilder.build();

      it('should render the rows', () => {
        const { wrapper } = setup({ columns });
        const expected = columns.length;
        const actual = wrapper.find('.table-detail-table .ams-table-row')
          .length;

        expect(actual).toEqual(expected);
      });

      it('should render the usage column', () => {
        const { wrapper } = setup({ columns });
        const expected = columns.length;
        const actual = wrapper.find('.table-detail-table .usage-value').length;

        expect(actual).toEqual(expected);
      });

      it('should render the actions column', () => {
        const { wrapper } = setup({ columns });
        const expected = columns.length;
        const actual = wrapper.find('.table-detail-table .actions').length;

        expect(actual).toEqual(expected);
      });

      describe('when usage sorting is passed', () => {
        it('should sort the data by that value', () => {
          const { wrapper } = setup({
            columns,
            sortBy: {
              name: 'Usage',
              key: 'usage',
              direction: SortDirection.descending,
            },
          });
          const expected = 'simple_column_name_timestamp';
          const actual = wrapper
            .find('.table-detail-table .ams-table-row')
            .at(0)
            .find('.column-name')
            .text();

          expect(actual).toEqual(expected);
        });
      });

      describe('when default sorting is passed', () => {
        it('should sort the data by that value', () => {
          const { wrapper } = setup({
            columns,
            sortBy: {
              name: 'Default',
              key: 'sort_order',
              direction: SortDirection.ascending,
            },
          });
          const expected = 'simple_column_name_string';
          const actual = wrapper
            .find('.table-detail-table .ams-table-row')
            .at(0)
            .find('.column-name')
            .text();

          expect(actual).toEqual(expected);
        });
      });

      describe('when name sorting is passed', () => {
        it('should sort the data by name', () => {
          const { wrapper } = setup({
            columns,
            sortBy: {
              name: 'Name',
              key: 'name',
              direction: SortDirection.descending,
            },
          });
          const expected = 'simple_column_name_bigint';
          const actual = wrapper
            .find('.table-detail-table .ams-table-row')
            .at(0)
            .find('.column-name')
            .text();

          expect(actual).toEqual(expected);
        });
      });
    });

    describe('when complex type columns are passed', () => {
      const { columns } = dataBuilder.withAllComplexColumns().build();

      it('should render the rows', () => {
        const { wrapper } = setup({ columns });
        const expected = columns.length;
        const actual = wrapper.find('.table-detail-table .ams-table-row')
          .length;

        expect(actual).toEqual(expected);
      });

      it('should render ColumnType components', () => {
        const { wrapper } = setup({ columns });
        const expected = columns.length;
        const actual = wrapper.find(ColumnType).length;

        expect(actual).toEqual(expected);
      });
    });

    describe('when columns with no usage data are passed', () => {
      const { columns } = dataBuilder.withComplexColumnsNoStats().build();

      it('should render the rows', () => {
        const { wrapper } = setup({ columns });
        const expected = columns.length;
        const actual = wrapper.find('.table-detail-table .ams-table-row')
          .length;

        expect(actual).toEqual(expected);
      });

      it('should not render the usage column', () => {
        const { wrapper } = setup({ columns });
        const expected = 0;
        const actual = wrapper.find('.table-detail-table .usage-value').length;

        expect(actual).toEqual(expected);
      });
    });

    describe('when columns with one usage data entry are passed', () => {
      const { columns } = dataBuilder.withComplexColumnsOneStat().build();

      it('should render the usage column', () => {
        const { wrapper } = setup({ columns });
        const expected = columns.length;
        const actual = wrapper.find('.table-detail-table .usage-value').length;

        expect(actual).toEqual(expected);
      });
    });

    describe('when columns with several stats including usage are passed', () => {
      const { columns } = dataBuilder.withSeveralStats().build();

      it('should render the usage column', () => {
        const { wrapper } = setup({ columns });
        const expected = columns.length;
        const actual = wrapper.find('.table-detail-table .usage-value').length;

        expect(actual).toEqual(expected);
      });

      describe('when usage sorting is passed', () => {
        it('should sort the data by that value', () => {
          const { wrapper } = setup({
            columns,
            sortBy: {
              name: 'Usage',
              key: 'usage',
              direction: SortDirection.ascending,
            },
          });
          const expected = 'complex_column_name_2';
          const actual = wrapper
            .find('.table-detail-table .ams-table-row')
            .at(0)
            .find('.column-name')
            .text();

          expect(actual).toEqual(expected);
        });
      });
    });

    describe('when notifications are not enabled', () => {
      const { columns } = dataBuilder.build();

      it('should not render the actions column', () => {
        mockedNotificationsEnabled.mockReturnValue(false);
        const { wrapper } = setup({ columns });
        const expected = 0;
        const actual = wrapper.find('.table-detail-table .actions').length;

        expect(actual).toEqual(expected);
      });
    });

    describe('when columns with badges are passed', () => {
      const { columns } = dataBuilder.withBadges().build();
      const getBadgeConfigSpy = jest.spyOn(ConfigUtils, 'getBadgeConfig');
      getBadgeConfigSpy.mockImplementation((badgeName: string) => ({
        displayName: badgeName + ' test name',
        style: BadgeStyle.PRIMARY,
      }));

      it('should render the rows', () => {
        const { wrapper } = setup({ columns });
        const expected = columns.length;
        const actual = wrapper.find('.table-detail-table .ams-table-row')
          .length;

        expect(actual).toEqual(expected);
      });

      it('should render the badge column', () => {
        const { wrapper } = setup({ columns });
        const expected = columns.length;
        const actual = wrapper.find('.badge-list').length;

        expect(actual).toEqual(expected);
      });

      describe('number of bages', () => {
        it('should render no badges in the first cell', () => {
          const { wrapper } = setup({ columns });
          const expected = 0;
          const actual = wrapper.find('.badge-list').at(0).find('.flag').length;

          expect(actual).toEqual(expected);
        });

        it('should render one badge in the second cell', () => {
          const { wrapper } = setup({ columns });
          const expected = 1;
          const actual = wrapper.find('.badge-list').at(1).find('.flag').length;

          expect(actual).toEqual(expected);
        });

        it('should render three badges in the third cell', () => {
          const { wrapper } = setup({ columns });
          const expected = 3;
          const actual = wrapper.find('.badge-list').at(2).find('.flag').length;

          expect(actual).toEqual(expected);
        });
      });
    });
  });
});
