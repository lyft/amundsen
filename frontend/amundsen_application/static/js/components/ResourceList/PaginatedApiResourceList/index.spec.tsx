// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import Pagination from 'react-js-pagination';
import { shallow } from 'enzyme';

import { ResourceType } from 'interfaces';
import ResourceListItem from 'components/ResourceListItem/index';

import PaginatedApiResourceList, { PaginatedApiResourceListProps } from '.';

describe('PaginatedApiResourceList', () => {
  const setStateSpy = jest.spyOn(
    PaginatedApiResourceList.prototype,
    'setState'
  );
  const setup = (propOverrides?: Partial<PaginatedApiResourceListProps>) => {
    const props: PaginatedApiResourceListProps = {
      activePage: 3,
      itemsPerPage: 4,
      onPagination: jest.fn(),
      slicedItems: [
        { type: ResourceType.table },
        { type: ResourceType.table },
        { type: ResourceType.table },
        { type: ResourceType.table },
      ],
      totalItemsCount: 40,
      source: 'testSource',
      ...propOverrides,
    };
    const wrapper = shallow<PaginatedApiResourceList>(
      // eslint-disable-next-line react/jsx-props-no-spreading
      <PaginatedApiResourceList {...props} />
    );
    return { props, wrapper };
  };

  describe('onPagination', () => {
    it('calls the onPagination prop', () => {
      const setupResult = setup();
      const { wrapper } = setupResult;
      const { props } = setupResult;
      const onPaginationSpy = jest.spyOn(props, 'onPagination');
      wrapper.instance().onPagination(3);
      expect(onPaginationSpy).toHaveBeenCalledWith(2);
    });
  });

  describe('render', () => {
    let props;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });

    it('renders empty messages if it exists and there are no items', () => {
      const { props, wrapper } = setup({
        totalItemsCount: 0,
        emptyText: 'Nothing Here',
      });
      expect(wrapper.find('.empty-message').text()).toBe(props.emptyText);
    });

    it('renders all slicedItems', () => {
      const items = wrapper.find(ResourceListItem);
      expect(items.length).toEqual(props.slicedItems.length);
    });

    it('renders pagination widget when totalItemsCount is greater than itemsPerPage', () => {
      expect(wrapper.find(Pagination).exists()).toBe(true);
    });

    it('hides pagination widget when totalItemsCount is less than itemsPerPage', () => {
      const { props, wrapper } = setup({ totalItemsCount: 2, itemsPerPage: 3 });
      expect(wrapper.find(Pagination).exists()).toBe(false);
    });
  });
});
