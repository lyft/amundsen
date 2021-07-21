// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import Pagination from 'react-js-pagination';
import { shallow } from 'enzyme';

import { ResourceType } from 'interfaces';
import ResourceListItem from 'components/ResourceListItem/index';

import PaginatedResourceList, { PaginatedResourceListProps } from '.';

describe('PaginatedResourceList', () => {
  const setStateSpy = jest.spyOn(PaginatedResourceList.prototype, 'setState');
  const setup = (propOverrides?: Partial<PaginatedResourceListProps>) => {
    const props: PaginatedResourceListProps = {
      allItems: [
        { type: ResourceType.table },
        { type: ResourceType.table },
        { type: ResourceType.table },
        { type: ResourceType.table },
        { type: ResourceType.table },
        { type: ResourceType.table },
      ],
      itemsPerPage: 4,
      source: 'testSource',
      ...propOverrides,
    };
    const wrapper = shallow<PaginatedResourceList>(
      <PaginatedResourceList {...props} />
    );
    return { props, wrapper };
  };

  describe('componentDidUpdate', () => {
    it('updates activePage state if the activePage is out of bounds by multiple pages', () => {
      const { wrapper } = setup({ itemsPerPage: 2 });
      wrapper.setState({ activePage: 2 });
      wrapper.setProps({
        allItems: [{ type: ResourceType.table }, { type: ResourceType.table }],
      });
      expect(wrapper.state().activePage).toEqual(0);
    });

    it('updates activePage state if the activePage is out of bounds by one page', () => {
      const { wrapper } = setup({ itemsPerPage: 2 });
      wrapper.setState({ activePage: 2 });
      wrapper.setProps({
        allItems: [
          { type: ResourceType.table },
          { type: ResourceType.table },
          { type: ResourceType.table },
        ],
      });
      expect(wrapper.state().activePage).toEqual(1);
    });

    it('does not update activePage if new values are not out of bounds', () => {
      const { wrapper } = setup({ itemsPerPage: 2 });
      wrapper.setState({ activePage: 2 });
      wrapper.setProps({
        allItems: [
          { type: ResourceType.table },
          { type: ResourceType.table },
          { type: ResourceType.table },
          { type: ResourceType.table },
          { type: ResourceType.table },
        ],
      });
      expect(wrapper.state().activePage).toEqual(2);
    });
  });

  describe('onPagination', () => {
    it('calls setState to update the activePage', () => {
      setStateSpy.mockClear();
      const { wrapper } = setup();
      wrapper.instance().onPagination(3);
      expect(setStateSpy).toHaveBeenCalledWith({ activePage: 2 });
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
        allItems: [],
        emptyText: 'Nothing Here',
      });
      expect(wrapper.find('.empty-message').text()).toBe(props.emptyText);
    });

    it('renders at most itemsPerPage ResourceListItems', () => {
      const items = wrapper.find(ResourceListItem);
      expect(items.length).toEqual(props.itemsPerPage);
    });

    it('renders a pagination widget when there are more than itemsPerPage items', () => {
      expect(wrapper.find(Pagination).exists()).toBe(true);
    });

    it('hides a pagination widget when there are fewer than itemsPerPage items', () => {
      const { props, wrapper } = setup({ itemsPerPage: 20 });
      expect(wrapper.find(Pagination).exists()).toBe(false);
    });
  });
});
