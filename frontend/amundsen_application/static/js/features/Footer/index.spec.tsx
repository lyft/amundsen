// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import globalState from 'fixtures/globalState';

import * as DateUtils from 'utils/dateUtils';
import { Footer, FooterProps, mapDispatchToProps, mapStateToProps } from '.';

const MOCK_DATE_STRING = 'Jan 1 2000 at 0:00:00 am';
jest.spyOn(DateUtils, 'formatDateTimeLong').mockReturnValue(MOCK_DATE_STRING);

describe('Footer', () => {
  let props: FooterProps;
  let wrapper;

  beforeEach(() => {
    props = {
      lastIndexed: 1555632106,
      getLastIndexed: jest.fn(),
    };
    wrapper = shallow(<Footer {...props} />);
  });

  describe('componentDidMount', () => {
    it('calls props.getLastIndexed', () => {
      expect(props.getLastIndexed).toHaveBeenCalled();
    });
  });

  describe('render', () => {
    it('calls generateDateTimeString if this.state.lastIndexed', () => {
      jest.spyOn(wrapper.instance(), 'generateDateTimeString');
      wrapper.instance().render();
      expect(wrapper.instance().generateDateTimeString).toHaveBeenCalled();
    });

    it('renders correct content if this.state.lastIndexed', () => {
      const expectedText = `Amundsen was last indexed on ${MOCK_DATE_STRING}`;

      expect(wrapper.find('#footer').props().children).toBeTruthy();
      expect(wrapper.find('#footer').text()).toEqual(expectedText);
    });

    describe('when state.lastIndexed is falsy', () => {
      it('renders the shimmering loader if this.state.lastIndexed is null', () => {
        const expected = 1;

        wrapper.setProps({ lastIndexed: null });

        expect(wrapper.find('ShimmeringFooterLoader').length).toEqual(expected);
      });

      it('renders the shimmering loader if this.state.lastIndexed is undefined', () => {
        const expected = 1;

        wrapper.setProps({ lastIndexed: undefined });

        expect(wrapper.find('ShimmeringFooterLoader').length).toEqual(expected);
      });
    });
  });
});

describe('mapDispatchToProps', () => {
  let dispatch;
  let result;

  beforeEach(() => {
    dispatch = jest.fn(() => Promise.resolve());
    result = mapDispatchToProps(dispatch);
  });

  it('sets getLastIndexed on the props', () => {
    expect(result.getLastIndexed).toBeInstanceOf(Function);
  });
});

describe('mapStateToProps', () => {
  let result;
  beforeEach(() => {
    result = mapStateToProps(globalState);
  });

  it('sets lastIndexed on the props', () => {
    expect(result.lastIndexed).toEqual(globalState.lastIndexed.lastIndexed);
  });
});
