// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import { GlobalState } from 'ducks/rootReducer';

import globalState from 'fixtures/globalState';

import { FilterType, ResourceType } from 'interfaces';
import { APPLY_BTN_TEXT } from '../constants';
import {
  InputFilter,
  InputFilterProps,
  mapDispatchToProps,
  mapStateToProps,
} from '.';

describe('InputFilter', () => {
  const setStateSpy = jest.spyOn(InputFilter.prototype, 'setState');

  const setup = (propOverrides?: Partial<InputFilterProps>) => {
    const props: InputFilterProps = {
      categoryId: 'schema',
      value: 'schema_name',
      updateFilter: jest.fn(),
      ...propOverrides,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow<InputFilter>(<InputFilter {...props} />);
    return {
      props,
      wrapper,
    };
  };

  describe('constructor', () => {
    const testValue = 'test';
    let wrapper;
    beforeAll(() => {
      wrapper = setup({ value: testValue }).wrapper;
    });
    it('sets the value state from props', () => {
      expect(wrapper.state().value).toEqual(testValue);
    });
  });

  describe('componentDidUpdate', () => {
    let props;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });
    it('sets the value state to props.value if the property has changed', () => {
      setStateSpy.mockClear();
      const newProps = {
        ...props,
        value: 'Some new value',
      };
      wrapper.setProps(newProps);
      expect(setStateSpy).toHaveBeenCalledWith({ value: newProps.value });
    });

    it('sets the value state to empty string if the property has change and is not truthy', () => {
      setStateSpy.mockClear();
      const newProps = {
        ...props,
        value: '',
      };
      wrapper.setProps(newProps);
      expect(setStateSpy).toHaveBeenCalledWith({ value: '' });
    });

    it('does not call set state if props.value has not changed', () => {
      wrapper.setProps(props);
      setStateSpy.mockClear();
      wrapper.setProps(props);
      expect(setStateSpy).not.toHaveBeenCalled();
    });
  });

  describe('onApplyChanges', () => {
    let props;
    let wrapper;

    let updateFilterSpy;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
      updateFilterSpy = jest.spyOn(props, 'updateFilter');
    });

    it('calls props.updateFilter if state.value is falsy', () => {
      updateFilterSpy.mockClear();
      wrapper.setState({ value: '' });
      wrapper.instance().onApplyChanges({ preventDefault: jest.fn() });
      expect(updateFilterSpy).toHaveBeenCalledWith(props.categoryId, undefined);
    });

    it('calls props.updateFilter if state.value has a truthy value', () => {
      updateFilterSpy.mockClear();
      const mockValue = 'hello';
      wrapper.setState({ value: mockValue });
      wrapper.instance().onApplyChanges({ preventDefault: jest.fn() });
      expect(updateFilterSpy).toHaveBeenCalledWith(props.categoryId, mockValue);
    });
  });

  describe('onInputChange', () => {
    let props;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });
    it('sets the value state to e.target.value', () => {
      setStateSpy.mockClear();
      const mockValue = 'mockValue';
      const expectedValue = 'mockvalue';
      const mockEvent = { target: { value: mockValue } };
      wrapper.instance().onInputChange(mockEvent);
      expect(setStateSpy).toHaveBeenCalledWith({ value: expectedValue });
    });
  });

  describe('render', () => {
    let props;
    let wrapper;
    let element;

    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
      wrapper.instance().render();
    });

    it('renders a form with correct onSubmit property', () => {
      element = wrapper.find('form');
      expect(element.props().onSubmit).toBe(wrapper.instance().onApplyChanges);
    });

    it('renders and input text with correct properties', () => {
      element = wrapper.find('input');
      expect(element.props().name).toBe(props.categoryId);
      expect(element.props().onChange).toBe(wrapper.instance().onInputChange);
      expect(element.props().value).toBe(wrapper.state().value);
    });

    it('renders a button with correct properties', () => {
      element = wrapper.find('button');
      expect(element.props().name).toBe(props.categoryId);
      expect(element.text()).toEqual(APPLY_BTN_TEXT);
    });
  });

  describe('mapStateToProps', () => {
    const mockCategoryId = 'schema';
    const { props } = setup({ categoryId: mockCategoryId });
    const mockFilters = 'schema_name';

    const mockStateWithFilters: GlobalState = {
      ...globalState,
      search: {
        ...globalState.search,
        resource: ResourceType.table,
        filters: {
          [ResourceType.table]: {
            [mockCategoryId]: mockFilters,
          },
        },
      },
    };

    const mockStateWithOutFilters: GlobalState = {
      ...globalState,
      search: {
        ...globalState.search,
        resource: ResourceType.user,
        filters: {
          [ResourceType.table]: {},
        },
      },
    };

    let result;
    beforeEach(() => {
      result = mapStateToProps(mockStateWithFilters, props);
    });

    it('sets value on the props with the filter value for the categoryId', () => {
      expect(result.value).toBe(mockFilters);
    });

    it('sets value to empty string if no filters exist for the given resource', () => {
      result = mapStateToProps(mockStateWithOutFilters, props);
      expect(result.value).toEqual('');
    });

    it('sets value to empty string if no filters exist for the given category', () => {
      const { props } = setup({ categoryId: 'fakeCategory' });
      result = mapStateToProps(mockStateWithFilters, props);
      expect(result.value).toEqual('');
    });
  });

  describe('mapDispatchToProps', () => {
    let dispatch;
    let result;
    beforeAll(() => {
      const { props } = setup();
      dispatch = jest.fn(() => Promise.resolve());
      result = mapDispatchToProps(dispatch);
    });

    it('sets updateFilter on the props', () => {
      expect(result.updateFilter).toBeInstanceOf(Function);
    });
  });
});
