// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import Breadcrumb from 'components/Breadcrumb';
import MyBookmarks from 'components/Bookmark/MyBookmarks';
import PopularTables from 'components/PopularResources';
import SearchBar from 'components/SearchBar';
import TagsListContainer from 'components/Tags';

import { getMockRouterProps } from 'fixtures/mockRouter';
import { mapDispatchToProps, HomePage, HomePageProps } from '.';

describe('HomePage', () => {
  const setup = (propOverrides?: Partial<HomePageProps>) => {
    const mockLocation = {
      search: '/search?searchTerm=testName&resource=table&pageIndex=1',
    };
    const routerProps = getMockRouterProps<any>(null, mockLocation);
    const props: HomePageProps = {
      searchReset: jest.fn(),
      ...routerProps,
      ...propOverrides,
    };
    const wrapper = shallow<HomePage>(<HomePage {...props} />);
    return { props, wrapper };
  };
  let props;
  let wrapper;
  beforeAll(() => {
    const setupResult = setup();
    props = setupResult.props;
    wrapper = setupResult.wrapper;
  });

  describe('render', () => {
    it('contains Searchbar', () => {
      expect(wrapper.contains(<SearchBar />));
    });

    it('contains a Breadcrumb that directs to the /search', () => {
      const element = wrapper.find(Breadcrumb);
      expect(element.exists()).toBe(true);
      expect(element.props().path).toEqual('/search');
    });

    it('contains TagsList', () => {
      expect(wrapper.contains(<TagsListContainer shortTagsList />));
    });

    it('contains MyBookmarks', () => {
      expect(wrapper.contains(<MyBookmarks />));
    });

    it('contains PopularResources', () => {
      expect(wrapper.contains(<PopularTables />));
    });
  });

  describe('componentDidMount', () => {
    it('calls searchReset', () => {
      const searchResetSpy = jest.spyOn(props, 'searchReset');
      wrapper.instance().componentDidMount();
      expect(searchResetSpy).toHaveBeenCalled();
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

  it('sets searchReset on the props', () => {
    expect(result.searchReset).toBeInstanceOf(Function);
  });
});
