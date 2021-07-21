// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';
import { mocked } from 'ts-jest/utils';

import globalState from 'fixtures/globalState';
import { ResourceType } from 'interfaces';
import PaginatedResourceList from 'components/ResourceList/PaginatedResourceList';
import TabsComponent from 'components/TabsComponent';
import { indexDashboardsEnabled } from 'config/config-utils';
import {
  BOOKMARK_TITLE,
  BOOKMARKS_PER_PAGE,
  EMPTY_BOOKMARK_MESSAGE,
  MY_BOOKMARKS_SOURCE_NAME,
} from './constants';
import { MyBookmarks, MyBookmarksProps, mapStateToProps } from '.';

jest.mock('config/config-utils', () => ({
  getDisplayNameByResource: jest.fn(() => 'Resource'),
  indexDashboardsEnabled: jest.fn(),
}));

describe('MyBookmarks', () => {
  const setStateSpy = jest.spyOn(MyBookmarks.prototype, 'setState');

  const setup = (propOverrides?: Partial<MyBookmarksProps>) => {
    const props: MyBookmarksProps = {
      myBookmarks: {
        [ResourceType.table]: [
          {
            key: 'bookmark-1',
            type: ResourceType.table,
            cluster: 'cluster',
            database: 'database',
            description: 'description',
            name: 'name',
            schema: 'schema',
          },
          {
            key: 'bookmark-2',
            type: ResourceType.table,
            cluster: 'cluster',
            database: 'database',
            description: 'description',
            name: 'name',
            schema: 'schema',
          },
          {
            key: 'bookmark-3',
            type: ResourceType.table,
            cluster: 'cluster',
            database: 'database',
            description: 'description',
            name: 'name',
            schema: 'schema',
          },
          {
            key: 'bookmark-4',
            type: ResourceType.table,
            cluster: 'cluster',
            database: 'database',
            description: 'description',
            name: 'name',
            schema: 'schema',
          },
          {
            key: 'bookmark-5',
            type: ResourceType.table,
            cluster: 'cluster',
            database: 'database',
            description: 'description',
            name: 'name',
            schema: 'schema',
          },
          {
            key: 'bookmark-6',
            type: ResourceType.table,
            cluster: 'cluster',
            database: 'database',
            description: 'description',
            name: 'name',
            schema: 'schema',
          },
        ],
        [ResourceType.dashboard]: [],
      },
      isLoaded: true,
      ...propOverrides,
    };
    const wrapper = shallow<MyBookmarks>(<MyBookmarks {...props} />);
    return { props, wrapper };
  };

  describe('generateTabContent', () => {
    let props;
    let wrapper;
    let givenResource;
    let content;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
      givenResource = ResourceType.table;
      content = shallow(
        <div>{wrapper.instance().generateTabContent(givenResource)}</div>
      );
    });

    it('returns a PaginatedResourceList with correct props', () => {
      const element = content.find(PaginatedResourceList);
      expect(element.props().allItems).toBe(props.myBookmarks[givenResource]);
      expect(element.props().itemsPerPage).toBe(BOOKMARKS_PER_PAGE);
      expect(element.props().source).toBe(MY_BOOKMARKS_SOURCE_NAME);
      expect(element.props().emptyText).toBe(EMPTY_BOOKMARK_MESSAGE);
    });

    it('returns undefined if there are no bookmarks to render', () => {
      content = wrapper.instance().generateTabContent(ResourceType.user);
      expect(content).toBeUndefined();
    });
  });

  describe('generateTabKey', () => {
    it('returns string used for the tab keys', () => {
      const { wrapper } = setup();
      const givenResource = ResourceType.table;
      expect(wrapper.instance().generateTabKey(givenResource)).toEqual(
        `bookmarktab:${givenResource}`
      );
    });
  });

  describe('generateTabTitle', () => {
    let wrapper;
    beforeAll(() => {
      wrapper = setup().wrapper;
    });
    it('returns string for tab title according to UI designs', () => {
      const givenResource = ResourceType.table;
      expect(wrapper.instance().generateTabTitle(givenResource)).toEqual(
        'Resource (6)'
      );
    });

    it('returns empty string if there are no bookmarks', () => {
      expect(wrapper.instance().generateTabTitle(ResourceType.user)).toEqual(
        ''
      );
    });
  });

  describe('generateTabInfo', () => {
    let tabInfoArray;
    let wrapper;
    let generateTabContentSpy;
    let generateTabKeySpy;
    let generateTabTitleSpy;

    beforeAll(() => {
      const setupResult = setup();
      wrapper = setupResult.wrapper;

      generateTabContentSpy = jest
        .spyOn(wrapper.instance(), 'generateTabContent')
        .mockImplementation((input) => `${input}Content`);
      generateTabKeySpy = jest
        .spyOn(wrapper.instance(), 'generateTabKey')
        .mockImplementation((input) => `${input}Key`);
      generateTabTitleSpy = jest
        .spyOn(wrapper.instance(), 'generateTabTitle')
        .mockImplementation((input) => `${input}Title`);
    });

    describe('pushes tab info for tables', () => {
      let tableTab;
      beforeAll(() => {
        tabInfoArray = wrapper.instance().generateTabInfo();
        tableTab = tabInfoArray.find((tab) => tab.key === 'tableKey');
      });

      it('generates content for table tab info', () => {
        expect(generateTabContentSpy).toHaveBeenCalledWith(ResourceType.table);
        expect(tableTab.content).toBe('tableContent');
      });

      it('generates key for table tab info', () => {
        expect(generateTabKeySpy).toHaveBeenCalledWith(ResourceType.table);
        expect(tableTab.key).toBe('tableKey');
      });

      it('generates title for table tab info', () => {
        expect(generateTabTitleSpy).toHaveBeenCalledWith(ResourceType.table);
        expect(tableTab.title).toBe('tableTitle');
      });
    });

    describe('handle tab info for dashboards', () => {
      let dashboardTab;
      describe('if dashboards are not enabled', () => {
        it('does not render dashboard tab', () => {
          mocked(indexDashboardsEnabled).mockImplementationOnce(() => false);
          tabInfoArray = wrapper.instance().generateTabInfo();
          expect(tabInfoArray.find((tab) => tab.key === 'dashboardKey')).toBe(
            undefined
          );
        });
      });

      describe('if dashboards are enabled', () => {
        beforeAll(() => {
          mocked(indexDashboardsEnabled).mockImplementationOnce(() => true);
          tabInfoArray = wrapper.instance().generateTabInfo();
          dashboardTab = tabInfoArray.find((tab) => tab.key === 'dashboardKey');
        });

        it('generates content for table tab info', () => {
          expect(generateTabContentSpy).toHaveBeenCalledWith(
            ResourceType.dashboard
          );
          expect(dashboardTab.content).toBe('dashboardContent');
        });

        it('generates key for table tab info', () => {
          expect(generateTabKeySpy).toHaveBeenCalledWith(
            ResourceType.dashboard
          );
          expect(dashboardTab.key).toBe('dashboardKey');
        });

        it('generates title for table tab info', () => {
          expect(generateTabTitleSpy).toHaveBeenCalledWith(
            ResourceType.dashboard
          );
          expect(dashboardTab.title).toBe('dashboardTitle');
        });
      });
    });
  });

  describe('render', () => {
    let wrapper;

    beforeAll(() => {
      const setupResult = setup();

      wrapper = setupResult.wrapper;
    });

    it('renders a shimmer loader until ready', () => {
      const { wrapper } = setup({ isLoaded: false });
      const expected = 1;
      const actual = wrapper.find('ShimmeringResourceLoader').length;

      expect(actual).toEqual(expected);
    });

    it('renders the correct title', () => {
      const { wrapper } = setup();
      const expected = BOOKMARK_TITLE;
      const actual = wrapper.find('.bookmark-list-header').text();

      expect(actual).toEqual(expected);
    });

    it('renders a TabsComponent with correct props', () => {
      jest
        .spyOn(wrapper.instance(), 'generateTabKey')
        .mockImplementation((input) => `${input}Key`);

      wrapper.instance().forceUpdate();

      expect(wrapper.find(TabsComponent).props()).toMatchObject({
        tabs: wrapper.instance().generateTabInfo(),
        defaultTab: 'tableKey',
      });
    });
  });
});

describe('mapStateToProps', () => {
  let result;
  beforeAll(() => {
    result = mapStateToProps(globalState);
  });

  it('sets bookmarks on the props', () => {
    expect(result.myBookmarks).toEqual(globalState.bookmarks.myBookmarks);
  });

  it('sets myBookmarksIsLoaded on the props', () => {
    expect(result.isLoaded).toEqual(globalState.bookmarks.myBookmarksIsLoaded);
  });
});
