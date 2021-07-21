// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { shallow } from 'enzyme';

import * as ConfigUtils from 'config/config-utils';
import { FilterConfig } from 'config/config-types';

import { FilterType, ResourceType } from 'interfaces';

import globalState from 'fixtures/globalState';
import { GlobalState } from 'ducks/rootReducer';

import {
  mapStateToProps,
  SearchFilter,
  SearchFilterProps,
  FilterSectionItem,
  CheckboxFilterSection,
} from '.';

describe('SearchFilter', () => {
  const setup = (propOverrides?: Partial<SearchFilterProps>) => {
    const props = {
      filterSections: [
        {
          categoryId: 'database',
          helpText: 'This is what to do',
          options: [
            {
              value: 'bigquery',
              label: 'BigQuery',
            },
            {
              value: 'hive',
              label: 'Hive',
            },
          ],
          title: 'Source',
          type: FilterType.CHECKBOX_SELECT,
        },
        {
          categoryId: 'schema',
          helpText: 'This is what to do',
          title: 'Schema',
          type: FilterType.INPUT_SELECT,
        },
      ],
      ...propOverrides,
    };
    // eslint-disable-next-line react/jsx-props-no-spreading
    const wrapper = shallow<SearchFilter>(<SearchFilter {...props} />);
    return {
      props,
      wrapper,
    };
  };

  describe('createFilterSection', () => {
    let props;
    let wrapper;
    let content;
    let mockCheckboxFilterData: CheckboxFilterSection;
    let mockInputFilterData: FilterSectionItem;
    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
      mockCheckboxFilterData = props.filterSections[0];
      mockInputFilterData = props.filterSections[1];
      content = wrapper
        .instance()
        .createFilterSection('sectionKey', mockCheckboxFilterData);
    });

    describe('renders a FilterSection', () => {
      it('FilterSection exists', () => {
        expect(content.type.displayName).toBe('Connect(FilterSection)');
      });

      it('with correct categoryId', () => {
        expect(content.props.categoryId).toBe(
          mockCheckboxFilterData.categoryId
        );
      });

      it('with correct helpText', () => {
        expect(content.props.helpText).toBe(mockCheckboxFilterData.helpText);
      });

      it('with correct title', () => {
        expect(content.props.title).toBe(mockCheckboxFilterData.title);
      });

      it('with correct type', () => {
        expect(content.props.type).toBe(mockCheckboxFilterData.type);
      });

      it('with options if not supported for the filter type ', () => {
        expect(content.props.options).toBe(mockCheckboxFilterData.options);
      });

      it('without options if not supported for the filter type ', () => {
        const content = wrapper
          .instance()
          .createFilterSection('sectionKey', mockInputFilterData);
        expect(content.props.options).toBe(undefined);
      });
    });
  });

  describe('renderFilterSections', () => {
    let props;
    let wrapper;
    let createFilterSectionSpy;

    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;
      createFilterSectionSpy = jest.spyOn(
        wrapper.instance(),
        'createFilterSection'
      );
      wrapper.instance().renderFilterSections();
    });

    it('calls createFilterSection with correct key and section for each props.filterSections', () => {
      props.filterSections.forEach((section) => {
        expect(createFilterSectionSpy).toHaveBeenCalledWith(
          `section:${section.categoryId}`,
          section
        );
      });
    });
  });

  describe('render', () => {
    let wrapper;
    let renderFilterSectionsSpy;

    beforeAll(() => {
      const setupResult = setup();
      wrapper = setupResult.wrapper;
      renderFilterSectionsSpy = jest.spyOn(
        wrapper.instance(),
        'renderFilterSections'
      );
      wrapper.instance().render();
    });

    it('calls renderFilterSections', () => {
      expect(renderFilterSectionsSpy).toHaveBeenCalledTimes(1);
    });
  });
});

describe('mapStateToProps', () => {
  const mockHelpText = 'Help me';

  const mockSchemaId = 'schema';
  const mockSchemaValue = 'schema_name';
  const mockSchemaTitle = 'Schema';

  const mockDbId = 'database';
  const mockDbTitle = 'Source';

  const MOCK_CATEGORY_CONFIG: FilterConfig = [
    {
      categoryId: mockDbId,
      displayName: mockDbTitle,
      type: FilterType.CHECKBOX_SELECT,
      helpText: mockHelpText,
      options: [
        { value: 'bigquery', displayName: 'BigQuery' },
        { value: 'hive', displayName: 'Hive' },
      ],
    },
    {
      categoryId: mockSchemaId,
      displayName: mockSchemaTitle,
      helpText: mockHelpText,
      type: FilterType.INPUT_SELECT,
    },
  ];
  const mockStateWithFilters: GlobalState = {
    ...globalState,
    search: {
      ...globalState.search,
      resource: ResourceType.table,
      filters: {
        [ResourceType.table]: {
          [mockSchemaId]: mockSchemaValue,
          [mockDbId]: {
            hive: true,
          },
        },
      },
    },
  };
  let getFilterConfigByResourceSpy;
  let result;

  it('calls getFilterConfigByResource with resource', () => {
    getFilterConfigByResourceSpy = jest
      .spyOn(ConfigUtils, 'getFilterConfigByResource')
      .mockReturnValue(MOCK_CATEGORY_CONFIG);
    mapStateToProps(mockStateWithFilters);
    expect(getFilterConfigByResourceSpy).toHaveBeenCalledWith(
      mockStateWithFilters.search.resource
    );
  });

  it('sets expected filterSections on the result', () => {
    getFilterConfigByResourceSpy = jest
      .spyOn(ConfigUtils, 'getFilterConfigByResource')
      .mockReturnValue(MOCK_CATEGORY_CONFIG);
    result = mapStateToProps(mockStateWithFilters);
    expect(result.filterSections).toEqual([
      {
        categoryId: mockDbId,
        helpText: mockHelpText,
        options: [
          { label: 'BigQuery', value: 'bigquery' },
          { label: 'Hive', value: 'hive' },
        ],
        type: FilterType.CHECKBOX_SELECT,
        title: mockDbTitle,
      },
      {
        categoryId: mockSchemaId,
        helpText: mockHelpText,
        options: [],
        title: mockSchemaTitle,
        type: FilterType.INPUT_SELECT,
      },
    ]);
  });

  it('sets empty array on filterSections if there are no configured filterCategories', () => {
    getFilterConfigByResourceSpy = jest
      .spyOn(ConfigUtils, 'getFilterConfigByResource')
      .mockReturnValue(undefined);
    result = mapStateToProps(globalState);
    expect(result.filterSections).toEqual([]);
  });
});
