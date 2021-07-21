// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as History from 'history';

import { mount, shallow } from 'enzyme';

import globalState from 'fixtures/globalState';
import { getMockRouterProps } from 'fixtures/mockRouter';

import { ResourceType } from 'interfaces';
import {
  mapStateToProps,
  mapDispatchToProps,
  SearchBar,
  SearchBarProps,
} from '.';

document.addEventListener = jest.fn(() => {});
document.removeEventListener = jest.fn(() => {});

describe('SearchBar', () => {
  const submitMockEvent = { preventDefault: jest.fn() };
  const setStateSpy = jest.spyOn(SearchBar.prototype, 'setState');
  const setup = (
    propOverrides?: Partial<SearchBarProps>,
    useMount?: boolean,
    location?: Partial<History.Location>
  ) => {
    const routerProps = getMockRouterProps<any>(null, location);
    const props: SearchBarProps = {
      onInputChange: jest.fn(),
      onSelectInlineResult: jest.fn(),
      searchTerm: '',
      submitSearch: jest.fn(),
      ...routerProps,
      ...propOverrides,
    };
    const wrapper = useMount
      ? mount<SearchBar>(<SearchBar {...props} />)
      : shallow<SearchBar>(<SearchBar {...props} />);
    return { props, wrapper };
  };

  describe('constructor', () => {
    const searchTerm = 'data';
    let wrapper;
    beforeAll(() => {
      wrapper = setup({ searchTerm }).wrapper;
    });
    it('sets the searchTerm state from props', () => {
      expect(wrapper.state().searchTerm).toEqual(searchTerm);
    });
  });

  describe('clearSearchTerm', () => {
    it('sets the searchTerm to an empty string', () => {
      setStateSpy.mockClear();
      const initialSearchTerm = 'non empty search term';
      const { wrapper } = setup({ searchTerm: initialSearchTerm });
      expect(wrapper.state().searchTerm).toBe(initialSearchTerm);
      wrapper.instance().clearSearchTerm();
      expect(setStateSpy).toHaveBeenCalledWith({
        searchTerm: '',
        showTypeAhead: false,
      });
    });

    it('calls props.clearSearch if it is defined', () => {
      const { props, wrapper } = setup({
        searchTerm: 'test',
        clearSearch: jest.fn(),
      });
      const clearSearchSpy = jest.spyOn(props, 'clearSearch');
      wrapper.instance().clearSearchTerm();
      expect(clearSearchSpy).toHaveBeenCalled();
    });
  });

  describe('componentDidMount', () => {
    it('adds an event listener for updateTypeAhead to be called on mousedown', () => {
      const { wrapper } = setup({}, true);
      expect(document.addEventListener).toHaveBeenCalledWith(
        'mousedown',
        wrapper.instance().updateTypeAhead,
        false
      );
    });
  });

  describe('componentWillUnmount', () => {
    it('removes the event listener for updateTypeAhead', () => {
      const { wrapper } = setup({}, true);
      wrapper.instance().componentWillUnmount();
      expect(document.removeEventListener).toHaveBeenCalledWith(
        'mousedown',
        wrapper.instance().updateTypeAhead,
        false
      );
    });
  });

  describe('componentDidUpdate', () => {
    it('sets the searchTerm state when props update', () => {
      const { props, wrapper } = setup();
      const prevState = wrapper.state();
      props.searchTerm = 'newTerm';
      // @ts-ignore: Why does this work in other tests but complain here
      wrapper.setProps(props);
      expect(wrapper.state()).toMatchObject({
        ...prevState,
        searchTerm: 'newTerm',
      });
    });
  });

  describe('handleValueChange', () => {
    let props;
    let wrapper;
    let isFormValidSpy;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
      isFormValidSpy = jest.spyOn(wrapper.instance(), 'isFormValid');
    });

    describe('when form is not valid', () => {
      beforeAll(() => {
        isFormValidSpy.mockImplementation(() => false);
      });

      it('updates the searchTerm (for visual feedback) and hides type ahead', () => {
        setStateSpy.mockClear();
        const testTerm = 'hello';
        // @ts-ignore: mocked events throw type errors
        wrapper.instance().handleValueChange({ target: { value: testTerm } });
        expect(setStateSpy).toHaveBeenCalledWith({
          searchTerm: testTerm,
          showTypeAhead: false,
        });
      });
    });

    describe('when form is valid', () => {
      beforeAll(() => {
        isFormValidSpy.mockImplementation(() => true);
      });

      describe('if searchTerm has length', () => {
        const mockSearchTerm = 'I have Length';
        const expectedSearchTerm = 'i have length';
        it('calls setState with searchTerm as lowercase target value & showTypeAhead as true ', () => {
          setStateSpy.mockClear();
          // @ts-ignore: mocked events throw type errors
          wrapper
            .instance()
            .handleValueChange({ target: { value: mockSearchTerm } });
          expect(setStateSpy).toHaveBeenCalledWith({
            searchTerm: expectedSearchTerm,
            showTypeAhead: true,
          });
        });

        it('calls onInputChange with searchTerm as lowercase target value', () => {
          // @ts-ignore: mocked events throw type errors
          props.onInputChange.mockClear();
          wrapper
            .instance()
            .handleValueChange({ target: { value: mockSearchTerm } });
          expect(props.onInputChange).toHaveBeenCalledWith(expectedSearchTerm);
        });
      });

      describe('if searchTerm has zero length', () => {
        const mockSearchTerm = '';
        it('calls clearSearchTerm', () => {
          const clearSearchTermSpy = jest.spyOn(
            wrapper.instance(),
            'clearSearchTerm'
          );
          // @ts-ignore: mocked events throw type errors
          wrapper
            .instance()
            .handleValueChange({ target: { value: mockSearchTerm } });
          expect(clearSearchTermSpy).toHaveBeenCalled();
        });
      });
    });
  });

  describe('handleValueSubmit', () => {
    let props;
    let wrapper;
    let hideTypeAheadSpy;
    let isFormValidSpy;
    let submitSearchSpy;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
      hideTypeAheadSpy = jest.spyOn(wrapper.instance(), 'hideTypeAhead');
      isFormValidSpy = jest.spyOn(wrapper.instance(), 'isFormValid');
      submitSearchSpy = jest.spyOn(props, 'submitSearch');
    });

    it('calls event.preventDefault', () => {
      isFormValidSpy.mockImplementationOnce(() => true);
      submitMockEvent.preventDefault.mockClear();
      // @ts-ignore: mocked events throw type errors
      wrapper.instance().handleValueSubmit(submitMockEvent);
      expect(submitMockEvent.preventDefault).toHaveBeenCalled();
    });

    describe('if isFormValid', () => {
      it('submits with correct props', () => {
        isFormValidSpy.mockImplementationOnce(() => true);
        submitSearchSpy.mockClear();
        // @ts-ignore: mocked events throw type errors
        wrapper.instance().handleValueSubmit(submitMockEvent);
        expect(submitSearchSpy).toHaveBeenCalledWith(props.searchTerm);
      });

      it('calls hideTypeAhead', () => {
        isFormValidSpy.mockImplementationOnce(() => true);
        hideTypeAheadSpy.mockClear();
        // @ts-ignore: mocked events throw type errors
        wrapper.instance().handleValueSubmit(submitMockEvent);
        expect(hideTypeAheadSpy).toHaveBeenCalled();
      });
    });

    describe('if !isFormValid', () => {
      it('does not submit if !isFormValid()', () => {
        isFormValidSpy.mockImplementationOnce(() => false);
        submitSearchSpy.mockClear();
        // @ts-ignore: mocked events throw type errors
        wrapper.instance().handleValueSubmit(submitMockEvent);
        expect(submitSearchSpy).not.toHaveBeenCalled();
      });

      it('does not call hideTypeAhead if !isFormValid()', () => {
        isFormValidSpy.mockImplementationOnce(() => false);
        hideTypeAheadSpy.mockClear();
        // @ts-ignore: mocked events throw type errors
        wrapper.instance().handleValueSubmit(submitMockEvent);
        expect(hideTypeAheadSpy).not.toHaveBeenCalled();
      });
    });
  });

  describe('hideTypeAhead', () => {
    it('sets shouldShowTypeAhead to false', () => {
      setStateSpy.mockClear();
      const { wrapper } = setup();
      wrapper.instance().hideTypeAhead();
      expect(setStateSpy).toHaveBeenCalledWith({ showTypeAhead: false });
    });
  });

  describe('shouldShowTypeAhead', () => {
    it('returns true for non-zero length string', () => {
      const { wrapper } = setup();
      expect(wrapper.instance().shouldShowTypeAhead('test')).toEqual(true);
    });

    it('returns false for empty string', () => {
      const { wrapper } = setup();
      expect(wrapper.instance().shouldShowTypeAhead('')).toEqual(false);
    });
  });

  describe('onSelectInlineResult', () => {
    let props;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });
    it('calls hideTypeAhead', () => {
      const hideTypeAheadSpy = jest.spyOn(wrapper.instance(), 'hideTypeAhead');
      wrapper.update();
      wrapper.instance().onSelectInlineResult(ResourceType.table, false);
      expect(hideTypeAheadSpy).toHaveBeenCalled();
    });

    it('calls props.onSelectInlineResult with given parameters', () => {
      const givenResource = ResourceType.user;
      const givenBoolean = true;
      wrapper.instance().onSelectInlineResult(givenResource, givenBoolean);
      expect(props.onSelectInlineResult).toHaveBeenCalledWith(
        givenResource,
        wrapper.state().searchTerm,
        givenBoolean
      );
    });
  });

  describe('updateTypeAhead', () => {
    /* TODO: How to test logic that leverages refs */
  });

  describe('isFormValid', () => {
    /* TODO: How to test logic that access document elements */
  });

  describe('render', () => {
    let props;
    let wrapper;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
    });

    describe('form', () => {
      it('renders with correct props', () => {
        expect(wrapper.find('form').props()).toMatchObject({
          id: 'search-bar-form',
          className: 'search-bar-form',
          onSubmit: wrapper.instance().handleValueSubmit,
        });
      });

      it('renders input with correct default props', () => {
        expect(wrapper.find('form').find('input').props()).toMatchObject({
          autoFocus: true,
          className: 'text-headline-w2 large search-bar-input form-control',
          id: 'search-input',
          onChange: wrapper.instance().handleValueChange,
          placeholder: SearchBar.defaultProps.placeholder,
          value: wrapper.state().searchTerm,
          required: true,
        });
      });

      it('renders input with correct given props', () => {
        const { props, wrapper } = setup({
          placeholder: 'Type something to search',
          searchTerm: 'data',
        });
        expect(wrapper.find('form').find('input').props()).toMatchObject({
          autoFocus: true,
          className: 'text-headline-w2 large search-bar-input form-control',
          id: 'search-input',
          onChange: wrapper.instance().handleValueChange,
          placeholder: props.placeholder,
          value: wrapper.state().searchTerm,
          required: true,
        });
      });

      describe('submit button', () => {
        it('renders button with correct props', () => {
          expect(wrapper.find('form').find('button').props()).toMatchObject({
            className: 'btn btn-flat-icon search-button large',
            type: 'submit',
          });
        });

        it('renders button img with correct props', () => {
          expect(
            wrapper.find('form').find('button').find('img').props()
          ).toMatchObject({
            className: 'icon icon-search',
          });
        });
      });
    });

    describe('render with small mode', () => {
      const { wrapper, props } = setup({ size: 'small' });
      it('renders a close button', () => {
        const closeButton = wrapper.find('button.clear-button');
        expect(closeButton.exists()).toBe(true);
        const buttonProps = closeButton.props();
        expect(buttonProps.onClick).toEqual(wrapper.instance().clearSearchTerm);
      });
    });
  });

  describe('mapDispatchToProps', () => {
    let dispatch;
    let result;
    beforeAll(() => {
      const { props } = setup();
      dispatch = jest.fn(() => Promise.resolve());
      result = mapDispatchToProps(dispatch, props);
    });

    it('sets submitSearch on the props', () => {
      /* TODO: How to test the boolean logic surrounding submitSearch */
      expect(result.submitSearch).toBeInstanceOf(Function);
    });
    it('sets onInputChange on the props', () => {
      expect(result.onInputChange).toBeInstanceOf(Function);
    });
    it('sets onSelectInlineResult on the props', () => {
      expect(result.onSelectInlineResult).toBeInstanceOf(Function);
    });
    it('sets clearSearch on the props if on search route', () => {
      const { props } = setup(undefined, undefined, { pathname: '/search' });
      result = mapDispatchToProps(dispatch, props);
      expect(result.clearSearch).toBeInstanceOf(Function);
    });
    it('does not seat clearSearch on the props if not on search route', () => {
      const { props } = setup();
      result = mapDispatchToProps(dispatch, props);
      expect(result.clearSearch).toBe(undefined);
    });
  });
});

describe('mapStateToProps', () => {
  let result;
  beforeAll(() => {
    result = mapStateToProps(globalState);
  });

  it('sets searchTerm on the props', () => {
    expect(result.searchTerm).toEqual(globalState.search.search_term);
  });
});
