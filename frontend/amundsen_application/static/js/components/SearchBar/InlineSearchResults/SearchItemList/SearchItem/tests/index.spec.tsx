// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import LoadingSpinner from 'components/LoadingSpinner';

import { SEARCH_ITEM_NO_RESULTS } from 'components/SearchBar/InlineSearchResults/constants';

import { ResourceType } from 'interfaces';

import { GlobalState } from 'ducks/rootReducer';
import globalState from 'fixtures/globalState';
import {
  allResourcesExample,
  isLoadingExample,
  noResultsExample,
} from 'fixtures/search/inlineResults';

import { SearchItem, SearchItemProps, mapStateToProps } from '..';

jest.mock('utils/analytics', () => ({
  logClick: jest.fn(() => {}),
}));

describe('SearchItem', () => {
  const setup = (propOverrides?: Partial<SearchItemProps>) => {
    const props: SearchItemProps = {
      listItemText: 'test',
      onItemSelect: jest.fn(),
      searchTerm: 'test search',
      resourceType: ResourceType.table,
      isLoading: false,
      hasResults: true,
      ...propOverrides,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow<SearchItem>(<SearchItem {...props} />);
    return {
      props,
      wrapper,
    };
  };

  describe('onViewAllResults', () => {
    it('calls props.onItemSelect with the correct parameters', () => {
      const { props, wrapper } = setup();
      const onItemSelectSpy = jest.spyOn(props, 'onItemSelect');
      wrapper.instance().onViewAllResults({});
      expect(onItemSelectSpy).toHaveBeenCalledWith(props.resourceType, true);
    });
  });

  describe('renderIndicator', () => {
    it('renders LoadingSpinner if props.isLoading', () => {
      const { wrapper } = setup({ isLoading: true });
      const content = shallow(
        <div>{wrapper.instance().renderIndicator()}</div>
      );
      expect(content.find(LoadingSpinner).exists()).toBe(true);
    });

    it('renders correct text if !props.hasResults', () => {
      const { wrapper } = setup({ hasResults: false });
      const rendered = wrapper.instance().renderIndicator();
      if (rendered === null) {
        throw Error('renderIndicator returned null');
      }
      expect(shallow(rendered).text()).toBe(SEARCH_ITEM_NO_RESULTS);
    });

    it('renders nothing if !props.Loading and props.hasResults', () => {
      const { wrapper } = setup({ isLoading: false, hasResults: true });
      expect(wrapper.instance().renderIndicator()).toBe(null);
    });
  });

  describe('render', () => {
    let props;
    let wrapper;
    let renderIndicatorSpy;
    let mockContent;
    beforeAll(() => {
      const setUpResult = setup();
      props = setUpResult.props;
      wrapper = setUpResult.wrapper;
      mockContent = <div>Hello</div>;
      renderIndicatorSpy = jest
        .spyOn(wrapper.instance(), 'renderIndicator')
        .mockImplementation(() => mockContent);
      wrapper.instance().forceUpdate();
    });

    describe('renders list item link', () => {
      let listItemLink;
      beforeAll(() => {
        listItemLink = wrapper.find('li').find('a');
      });

      it('with correct onClick interaction', () => {
        expect(listItemLink.props().onClick).toBe(
          wrapper.instance().onViewAllResults
        );
      });

      it('with correct class', () => {
        expect(listItemLink.hasClass('search-item-link')).toBe(true);
      });

      describe('with correct content', () => {
        it('renders an img with correct class', () => {
          expect(listItemLink.find('img').props().className).toEqual(
            'icon icon-search'
          );
        });

        it('renders correct text', () => {
          expect(listItemLink.find('.search-item-info').text()).toEqual(
            `${props.searchTerm}\u00a0${props.listItemText}`
          );
        });

        it('renders results of renderIndicator', () => {
          expect(listItemLink.children().at(2).html()).toEqual(
            '<div>Hello</div>'
          );
        });
      });
    });

    it('calls renderIndicator', () => {
      renderIndicatorSpy.mockClear();
      wrapper.instance().render();
      expect(renderIndicatorSpy).toHaveBeenCalledTimes(1);
    });
  });

  describe('mapStateToProps', () => {
    let result;
    let ownProps;
    const mockLoadingState: GlobalState = {
      ...globalState,
      search: {
        ...globalState.search,
        inlineResults: isLoadingExample,
      },
    };
    const mockAllResultsState: GlobalState = {
      ...globalState,
      search: {
        ...globalState.search,
        // @ts-ignore: https://github.com/microsoft/TypeScript/issues/10570
        inlineResults: allResourcesExample,
      },
    };
    const mockNoResultsState: GlobalState = {
      ...globalState,
      search: {
        ...globalState.search,
        inlineResults: noResultsExample,
      },
    };

    it('sets isLoading on the props', () => {
      ownProps = setup().props;
      result = mapStateToProps(mockLoadingState, ownProps);
      expect(result.isLoading).toEqual(true);
    });

    describe('ownProps.resourceType is ResourceType.table', () => {
      beforeAll(() => {
        ownProps = setup({ resourceType: ResourceType.table }).props;
      });
      it('sets hasResults to true if there are table results', () => {
        result = mapStateToProps(mockAllResultsState, ownProps);
        expect(result.hasResults).toEqual(true);
      });

      it('sets hasResults to false if there are no table results', () => {
        result = mapStateToProps(mockNoResultsState, ownProps);
        expect(result.hasResults).toEqual(false);
      });
    });

    describe('ownProps.resourceType is ResourceType.user', () => {
      beforeAll(() => {
        ownProps = setup({ resourceType: ResourceType.user }).props;
      });
      it('sets hasResults to true if there are user results', () => {
        result = mapStateToProps(mockAllResultsState, ownProps);
        expect(result.hasResults).toEqual(true);
      });

      it('sets hasResults to false if there are no user results', () => {
        result = mapStateToProps(mockNoResultsState, ownProps);
        expect(result.hasResults).toEqual(false);
      });
    });

    describe('ownProps.resourceType is ResourceType.dashboard', () => {
      beforeAll(() => {
        ownProps = setup({ resourceType: ResourceType.dashboard }).props;
      });
      it('sets hasResults to true if there are dashboard results', () => {
        result = mapStateToProps(mockAllResultsState, ownProps);
        expect(result.hasResults).toEqual(true);
      });

      it('sets hasResults to false if there are no dashboard results', () => {
        result = mapStateToProps(mockNoResultsState, ownProps);
        expect(result.hasResults).toEqual(false);
      });
    });
  });
});
