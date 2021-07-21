// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import { Preloader, PreloaderProps, mapDispatchToProps } from '.';

describe('Preloader', () => {
  const setup = (propOverrides?: Partial<PreloaderProps>) => {
    const props: PreloaderProps = {
      getLoggedInUser: jest.fn(),
      getBookmarks: jest.fn(),
      ...propOverrides,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow<Preloader>(<Preloader {...props} />);
    return {
      props,
      wrapper,
    };
  };

  describe('componentDidMount', () => {
    it('calls props.getLoggedInUser', () => {
      const { props, wrapper } = setup();
      wrapper.instance().componentDidMount();
      expect(props.getLoggedInUser).toHaveBeenCalled();
    });

    it('calls props.getLoggedInUser', () => {
      const { props, wrapper } = setup();
      wrapper.instance().componentDidMount();
      expect(props.getBookmarks).toHaveBeenCalled();
    });
  });

  describe('render', () => {
    it('does not render any elements', () => {
      const { wrapper } = setup();
      expect(wrapper.html()).toBeFalsy();
    });
  });
});

describe('mapDispatchToProps', () => {
  let dispatch;
  let props;

  beforeAll(() => {
    dispatch = jest.fn(() => Promise.resolve());
    props = mapDispatchToProps(dispatch);
  });

  it('sets getBookmarks on props', () => {
    expect(props.getBookmarks).toBeInstanceOf(Function);
  });

  it('sets getLoggedInUser on props', () => {
    expect(props.getLoggedInUser).toBeInstanceOf(Function);
  });
});
