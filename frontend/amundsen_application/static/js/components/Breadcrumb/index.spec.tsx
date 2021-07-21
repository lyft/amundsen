// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import { Link } from 'react-router-dom';
import { Breadcrumb, BreadcrumbProps, mapDispatchToProps } from '.';

describe('Breadcrumb', () => {
  const setup = (propOverrides?: Partial<BreadcrumbProps>) => {
    const props: BreadcrumbProps = {
      loadPreviousSearch: jest.fn(),
      ...propOverrides,
    };
    const wrapper = shallow(<Breadcrumb {...props} />);
    return { props, wrapper };
  };

  describe('render', () => {
    let props: BreadcrumbProps;
    let subject;

    describe('when given path & text', () => {
      beforeAll(() => {
        const setupResult = setup({ path: 'testPath', text: 'testText' });
        props = setupResult.props;
        subject = setupResult.wrapper;
      });

      it('renders Link with given path', () => {
        expect(subject.find(Link).props()).toMatchObject({
          to: props.path,
        });
      });

      it('renders Link with given text', () => {
        expect(subject.find(Link).find('span').text()).toEqual(props.text);
      });

      it('renders left icon by default', () => {
        expect(subject.find(Link).find('img').props().className).toEqual(
          'icon icon-left'
        );
      });

      it('renders left icon when props.direction = "left"', () => {
        subject = setup({
          path: 'testPath',
          text: 'testText',
          direction: 'left',
        }).wrapper;
        expect(subject.find(Link).find('img').props().className).toEqual(
          'icon icon-left'
        );
      });

      it('renders right icon when props.direction = "right"', () => {
        subject = setup({
          path: 'testPath',
          text: 'testText',
          direction: 'right',
        }).wrapper;
        expect(subject.find(Link).find('img').props().className).toEqual(
          'icon icon-right'
        );
      });
    });

    describe('when not given path or text', () => {
      beforeAll(() => {
        const setupResult = setup();
        props = setupResult.props;
        subject = setupResult.wrapper;
      });

      it('renders anchor tag with onClick method', () => {
        expect(subject.find('a').props()).toMatchObject({
          onClick: props.loadPreviousSearch,
        });
      });

      it('renders left icon by default', () => {
        expect(subject.find('a').find('img').props().className).toEqual(
          'icon icon-left'
        );
      });

      it('renders left icon when props.direction = "left"', () => {
        subject = setup({ direction: 'left' }).wrapper;
        expect(subject.find('a').find('img').props().className).toEqual(
          'icon icon-left'
        );
      });

      it('renders right icon when props.direction = "right"', () => {
        subject = setup({ direction: 'right' }).wrapper;
        expect(subject.find('a').find('img').props().className).toEqual(
          'icon icon-right'
        );
      });
    });
  });

  describe('mapDispatchToProps', () => {
    let dispatch;
    let result;
    beforeAll(() => {
      dispatch = jest.fn(() => Promise.resolve());
      result = mapDispatchToProps(dispatch);
    });

    it('sets loadPreviousSearch on the props', () => {
      expect(result.loadPreviousSearch).toBeInstanceOf(Function);
    });
  });
});
