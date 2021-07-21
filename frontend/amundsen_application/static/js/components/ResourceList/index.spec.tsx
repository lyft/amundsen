// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import { ResourceType } from 'interfaces';
import ResourceListItem from 'components/ResourceListItem/index';
import ResourceList, { ResourceListProps } from '.';

import * as CONSTANTS from './constants';

describe('ResourceList', () => {
  const setStateSpy = jest.spyOn(ResourceList.prototype, 'setState');
  const setup = (propOverrides?: Partial<ResourceListProps>) => {
    const props: ResourceListProps = {
      allItems: [
        {
          type: ResourceType.table,
        },
        {
          type: ResourceType.table,
        },
        {
          type: ResourceType.table,
        },
        {
          type: ResourceType.table,
        },
        {
          type: ResourceType.table,
        },
        {
          type: ResourceType.table,
        },
      ],
      itemsPerPage: 4,
      source: 'testSource',
      ...propOverrides,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow<ResourceList>(<ResourceList {...props} />);
    return {
      props,
      wrapper,
    };
  };

  describe('onViewAllToggle', () => {
    it('negates state.Expanded', () => {
      const { wrapper } = setup();
      const initialState = wrapper.state().isExpanded;
      wrapper.instance().onViewAllToggle();
      expect(wrapper.state().isExpanded).toEqual(!initialState);
      wrapper.instance().onViewAllToggle();
      expect(wrapper.state().isExpanded).toEqual(initialState);
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

    it('renders title if it exists', () => {
      const { props, wrapper } = setup({ title: 'I am a title' });
      expect(wrapper.find('.resource-list-title').text()).toBe(props.title);
    });

    it('renders empty messages if it exists and there are no items', () => {
      const { props, wrapper } = setup({
        allItems: [],
        emptyText: 'Nothing Here',
      });
      expect(wrapper.find('.empty-message').text()).toBe(props.emptyText);
    });

    it('should render all items if expanded', () => {
      wrapper.setState({ isExpanded: true });
      const items = wrapper.find(ResourceListItem);
      expect(items.length).toEqual(props.allItems.length);
    });

    it('should render items.length = itemsPerPage if not expanded', () => {
      wrapper.setState({ isExpanded: false });
      const items = wrapper.find(ResourceListItem);
      expect(items.length).toEqual(props.itemsPerPage);
    });

    it('passes correct props to each ResourceListItem', () => {
      const items = wrapper.find(ResourceListItem);
      items.forEach((contentItem, idx) => {
        expect(contentItem.props()).toMatchObject({
          item: props.allItems[idx],
          logging: {
            source: props.source,
            index: idx,
          },
        });
      });
    });

    describe('renders footer toggle link if num items > ITEMS_PER_PAGE', () => {
      let footerLink;
      beforeAll(() => {
        footerLink = wrapper.find('.resource-list-footer').find('a');
      });

      it('renders a link to toggle viewing items', () => {
        expect(footerLink.props().onClick).toEqual(
          wrapper.instance().onViewAllToggle
        );
      });

      it('renders correct default text if not expanded', () => {
        wrapper.setState({ isExpanded: false });
        expect(wrapper.find('.resource-list-footer').find('a').text()).toEqual(
          CONSTANTS.FOOTER_TEXT_COLLAPSED
        );
      });

      it('renders props.footerTextCollapsed if it exists and not expanded', () => {
        const { wrapper } = setup({ footerTextCollapsed: 'Hello' });
        expect(wrapper.find('.resource-list-footer').find('a').text()).toEqual(
          'Hello'
        );
      });

      it('renders correct default text if expanded', () => {
        wrapper.setState({ isExpanded: true });
        expect(wrapper.find('.resource-list-footer').find('a').text()).toEqual(
          CONSTANTS.FOOTER_TEXT_EXPANDED
        );
      });
    });
  });
});
