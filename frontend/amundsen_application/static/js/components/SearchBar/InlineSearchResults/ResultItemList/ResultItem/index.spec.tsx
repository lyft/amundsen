// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Link } from 'react-router-dom';

import { shallow } from 'enzyme';

import ResultItem, { ResultItemProps } from '.';

describe('ResultItem', () => {
  let props: ResultItemProps;
  let subject;

  beforeAll(() => {
    props = {
      id: 'foo',
      href: '/test',
      iconClass: 'test-icon',
      onItemSelect: jest.fn(),
      subtitle: 'subtitle',
      titleNode: <div>Hello</div>,
      type: 'User',
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    subject = shallow(<ResultItem {...props} />);
  });

  describe('render', () => {
    let link;
    beforeAll(() => {
      link = subject.find(Link);
    });

    it('renders Link with correct props', () => {
      expect(link.props().onClick).toEqual(props.onItemSelect);
      expect(link.props().to).toEqual(props.href);
    });

    it('renders icon with correct props', () => {
      expect(link.find('span').props().className).toEqual(
        `result-icon ${props.iconClass}`
      );
    });

    describe('renders result-info', () => {
      let resultInfo;
      let contentWrapper;
      beforeAll(() => {
        resultInfo = link.find('.result-info');
        contentWrapper = resultInfo.children().at(0);
      });

      it('truncates the text accordingly', () => {
        expect(contentWrapper.props().className).toMatch(/truncated/);
        expect(contentWrapper.children().at(1).props().className).toMatch(
          /truncated/
        );
      });

      it('renders the title', () => {
        expect(contentWrapper.children().at(0).text()).toEqual(
          // @ts-ignore: assertion passes but throws a TS error
          shallow(props.titleNode).text()
        );
      });

      it('renders the subtitle', () => {
        expect(contentWrapper.find('.body-secondary-3').text()).toEqual(
          props.subtitle
        );
      });
    });

    it('renders resource-type with correct text', () => {
      expect(link.find('.resource-type').text()).toEqual(props.type);
    });
  });
});
