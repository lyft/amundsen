// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import InfoButton from 'components/InfoButton';
import PaginatedResourceList from 'components/ResourceList/PaginatedResourceList';
import globalState from 'fixtures/globalState';
import { ResourceType } from 'interfaces/Resources';
import {
  POPULAR_RESOURCES_INFO_TEXT,
  POPULAR_RESOURCES_LABEL,
  POPULAR_RESOURCES_PER_PAGE,
  POPULAR_RESOURCES_SOURCE_NAME,
} from './constants';
import {
  PopularResources,
  PopularResourcesProps,
  mapStateToProps,
  mapDispatchToProps,
} from '.';

const setup = (propOverrides?: Partial<PopularResourcesProps>) => {
  const props: PopularResourcesProps = {
    isLoaded: false,
    popularResources: jest.fn() as any,
    getPopularResources: jest.fn(),
    ...propOverrides,
  };
  // eslint-disable-next-line react/jsx-props-no-spreading
  const wrapper = shallow<PopularResources>(<PopularResources {...props} />);

  return {
    props,
    wrapper,
  };
};

describe('popularResources', () => {
  let wrapper;
  let props;

  describe('componentDidMount', () => {
    let getpopularResourcesSpy;

    beforeAll(() => {
      ({ wrapper, props } = setup());

      getpopularResourcesSpy = jest.spyOn(props, 'getPopularResources');
    });

    it('calls getpopularResources', () => {
      expect(getpopularResourcesSpy).toHaveBeenCalled();
    });
  });

  describe('mapStateToProps', () => {
    it('sets popularResources on the props', () => {
      const actual = mapStateToProps(globalState).popularResources;
      const expected = globalState.popularResources.popularResources;

      expect(actual).toEqual(expected);
    });
  });

  describe('mapDispatchToProps', () => {
    let result;

    beforeAll(() => {
      const dispatch = jest.fn(() => Promise.resolve());
      result = mapDispatchToProps(dispatch);
    });

    it('sets getPopularResources on the props', () => {
      expect(result.getPopularResources).toBeInstanceOf(Function);
    });
  });

  describe('render', () => {
    beforeAll(() => {
      ({ wrapper, props } = setup());
    });

    it('renders correct label for content', () => {
      const expected = POPULAR_RESOURCES_LABEL;
      const actual = wrapper
        .children()
        .find('.popular-tables-header-text')
        .text();

      expect(actual).toEqual(expected);
    });

    it('renders InfoButton with correct props', () => {
      expect(wrapper.children().find(InfoButton).props()).toMatchObject({
        infoText: POPULAR_RESOURCES_INFO_TEXT,
      });
    });

    describe('when loading', () => {
      it('renders loading state', () => {
        const actual = wrapper.find('ShimmeringResourceLoader').length;
        const expected = 1;

        expect(actual).toEqual(expected);
      });
    });

    describe('when loaded', () => {
      let givenResource;
      let content;
      beforeAll(() => {
        ({ wrapper, props } = setup({
          isLoaded: true,
          popularResources: globalState.popularResources.popularResources,
        }));
        givenResource = ResourceType.table;
        content = shallow(
          <div>{wrapper.instance().generateTabContent(givenResource)}</div>
        );
      });

      it('renders PaginatedResourceList with correct props', () => {
        const actual = content.find(PaginatedResourceList).props();
        const expected = {
          allItems: props.popularResources[givenResource],
          itemsPerPage: POPULAR_RESOURCES_PER_PAGE,
          source: POPULAR_RESOURCES_SOURCE_NAME,
        };

        expect(actual).toMatchObject(expected);
      });
    });
  });
});
