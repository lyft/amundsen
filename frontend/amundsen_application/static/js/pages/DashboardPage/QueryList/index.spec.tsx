// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import { ResourceType } from 'interfaces';
import QueryList, { QueryListProps } from '.';
import QueryListItem from '../QueryListItem';

const setup = (propOverrides?: Partial<QueryListProps>) => {
  const props = {
    product: 'Mode',
    queries: [],
    ...propOverrides,
  };
  const wrapper = shallow<QueryList>(<QueryList {...props} />);

  return { props, wrapper };
};

describe('QueryList', () => {
  describe('render', () => {
    it('returns a list item for each query', () => {
      const { props, wrapper } = setup({
        queries: [
          {
            type: ResourceType.query,
            name: '2022-02-22 TEST QUERY NAME',
            query_text:
              "WITH\n\ncolumnName AS (\nSELECT  split_part(columnName, 'TEST', 2) as test",
            url:
              'https://app.mode.com/company/reports/testID/queries/testQuery',
          },
          {
            type: ResourceType.query,
            name: '2022-02-23 TEST QUERY NAME TWO',
            query_text:
              "WITH\n\ncolumnName AS (\nSELECT  split_part(columnName, 'TEST', 2) as test",
            url:
              'https://app.mode.com/company/reports/testID2/queries/testQuery2',
          },
        ],
      });
      const expected = props.queries.length;
      const actual = wrapper.find(QueryListItem).length;

      expect(actual).toEqual(expected);
    });

    describe('when no queries available', () => {
      it('returns null', () => {
        const { wrapper } = setup();
        const expected = 0;
        const actual = wrapper.find(QueryListItem).length;

        expect(actual).toEqual(expected);
      });
    });
  });
});
