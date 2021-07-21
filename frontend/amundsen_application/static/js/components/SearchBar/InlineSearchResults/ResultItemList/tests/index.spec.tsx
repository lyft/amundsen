// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import { ResourceType } from 'interfaces';
import ResultItemList, { ResultItemListProps } from '..';

import {
  RESULT_LIST_FOOTER_PREFIX,
  RESULT_LIST_FOOTER_SUFFIX,
} from '../../constants';

jest.mock('utils/analytics', () => ({
  logClick: jest.fn(() => {}),
}));

describe('ResultItemList', () => {
  const setup = (propOverrides?: Partial<ResultItemListProps>) => {
    const props: ResultItemListProps = {
      onItemSelect: jest.fn(),
      resourceType: ResourceType.table,
      searchTerm: 'test',
      suggestedResults: [
        {
          href: '/test',
          iconClass: 'test-icon',
          subtitle: 'subtitle',
          titleNode: 'title',
          type: 'Hive',
        },
        {
          href: '/test2',
          iconClass: 'test-icon',
          subtitle: 'subtitle2',
          titleNode: 'title2',
          type: 'Hive',
        },
      ],
      title: 'Datasets',
      totalResults: 10,
      ...propOverrides,
    };
    const wrapper = shallow<ResultItemList>(<ResultItemList {...props} />);
    return { props, wrapper };
  };

  describe('generateFooterLinkText', () => {
    it('returns the expected text', () => {
      const { props, wrapper } = setup();
      const output = wrapper.instance().generateFooterLinkText();
      expect(output).toEqual(
        `${RESULT_LIST_FOOTER_PREFIX} ${props.totalResults} ${props.title} ${RESULT_LIST_FOOTER_SUFFIX}`
      );
    });
  });

  describe('onViewAllResults', () => {
    it('calls props.onItemSelect with the correct parameters', () => {
      const { props, wrapper } = setup();
      const onItemSelectSpy = jest.spyOn(props, 'onItemSelect');
      wrapper.instance().onViewAllResults({});
      expect(onItemSelectSpy).toHaveBeenCalledWith(props.resourceType, true);
    });
  });

  describe('renderResultItems', () => {
    it('renders a ResultItem for item in the given results list', () => {
      const { props, wrapper } = setup();
      const listItems = wrapper
        .instance()
        .renderResultItems(props.suggestedResults);
      const expectedOnItemSelect = props.onItemSelect(props.resourceType);
      listItems.forEach((item, index) => {
        const {
          href,
          iconClass,
          subtitle,
          titleNode,
          type,
        } = props.suggestedResults[index];
        expect(item.props.href).toBe(href);
        expect(item.props.onItemSelect()).toBe(expectedOnItemSelect);
        expect(item.props.iconClass).toBe(`icon icon-dark ${iconClass}`);
        expect(item.props.subtitle).toBe(subtitle);
        expect(item.props.titleNode).toBe(titleNode);
        expect(item.props.type).toBe(type);
      });
    });
  });

  describe('render', () => {
    let props;
    let wrapper;

    let generateFooterLinkTextSpy;
    let renderResultItemsSpy;
    beforeAll(() => {
      const setUpResult = setup();
      props = setUpResult.props;
      wrapper = setUpResult.wrapper;
      generateFooterLinkTextSpy = jest
        .spyOn(wrapper.instance(), 'generateFooterLinkText')
        .mockImplementation(() => 'I am footer');
      renderResultItemsSpy = jest
        .spyOn(wrapper.instance(), 'renderResultItems')
        .mockImplementation(() => <li key="test">Hello</li>);
      wrapper.instance().forceUpdate();
    });

    describe('renders the title', () => {
      let title;
      beforeAll(() => {
        title = wrapper.find('.section-title');
      });
      it('with correct text', () => {
        expect(title.text()).toEqual(props.title);
      });
      it('with correct class', () => {
        expect(title.hasClass('title-3')).toBe(true);
      });
    });

    it('renders result items', () => {
      expect(renderResultItemsSpy).toHaveBeenCalledWith(props.suggestedResults);
    });

    describe('renders the footer', () => {
      let footer;
      beforeAll(() => {
        footer = wrapper.find('.section-footer');
      });
      it('with correct text', () => {
        expect(generateFooterLinkTextSpy).toHaveBeenCalled();
        expect(footer.text()).toEqual('I am footer');
      });
      it('with correct class', () => {
        expect(footer.hasClass('title-3')).toBe(true);
      });
      it('with correct onClick interaction', () => {
        expect(footer.props().onClick).toEqual(
          wrapper.instance().onViewAllResults
        );
      });
    });
  });
});
