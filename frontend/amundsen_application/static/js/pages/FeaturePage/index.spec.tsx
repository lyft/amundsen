// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0
import * as React from 'react';
import * as History from 'history';
import { shallow } from 'enzyme';

import globalState from 'fixtures/globalState';
import {
  featureCode,
  featureMetadata,
  featureLineage,
  previewData,
} from 'fixtures/metadata/feature';
import { previewDataSuccess } from 'fixtures/metadata/previewData';
import TabsComponent from 'components/TabsComponent';

import {
  FeaturePageLoader,
  FeaturePage,
  FeaturePageProps,
  mapDispatchToProps,
  mapStateToProps,
  getFeatureKey,
  renderTabs,
} from '.';

const setupLoader = () => {
  const wrapper = shallow(<FeaturePageLoader />);
  return wrapper;
};
describe('FeaturePageLoader', () => {
  it('should render without errors', () => {
    expect(() => {
      setupLoader();
    }).not.toThrow();
  });

  it('renders a mock header', () => {
    const wrapper = setupLoader();
    const expected = 1;
    const actual = wrapper.find('.resource-header').length;
    expect(actual).toEqual(expected);
  });

  it('renders three mock tabs', () => {
    const wrapper = setupLoader();
    const expected = 3;
    const actual = wrapper.find('.shimmer-tab').length;
    expect(actual).toEqual(expected);
  });
});

describe('renderTabs', () => {
  it('returns returns a tabs component', () => {
    const mockFeatureCode = featureCode;
    const mockFeatureLineage = featureLineage;
    const mockPreviewData = previewData;
    const result: JSX.Element = renderTabs(
      mockFeatureCode,
      mockFeatureLineage,
      mockPreviewData
    );
    expect(shallow(result).find(TabsComponent).exists).toBeTruthy();
  });
});

const setup = (
  propOverrides?: Partial<FeaturePageProps>,
  location?: Partial<History.Location>
) => {
  const props = {
    location,
    featureCode,
    isLoading: false,
    feature: featureMetadata,
    preview: previewDataSuccess,
    getFeatureDispatch: jest.fn(),
    getFeatureCodeDispatch: jest.fn(),
    ...propOverrides,
  };
  // @ts-ignore
  const wrapper = shallow<FeaturePage>(<FeaturePage {...props} />);
  return { props, wrapper };
};

// TODO - expand test coverage of this component
describe('FeaturePage', () => {
  it('does not throw', () => {
    expect(() => {
      setup();
    }).not.toThrow();
  });
});

describe('getFeatureKey', () => {
  it('returns the expected key format', () => {
    const mockGroup = 'test_group';
    const mockName = 'test_name';
    const mockVersion = '2';
    const expected = 'test_group/test_name/2';
    const actual = getFeatureKey(mockGroup, mockName, mockVersion);
    expect(actual).toEqual(expected);
  });
});

describe('mapStateToProps', () => {
  it('returns expected props', () => {
    const result = mapStateToProps(globalState);
    const { feature } = globalState;
    expect(result.isLoading).toEqual(feature.isLoading);
    expect(result.statusCode).toEqual(feature.statusCode);
    expect(result.feature).toEqual(feature.feature);
    expect(result.featureCode).toEqual(feature.featureCode);
  });
});

describe('mapDispatchToProps', () => {
  let dispatch;
  let result;
  beforeAll(() => {
    dispatch = jest.fn(() => Promise.resolve());
    result = mapDispatchToProps(dispatch);
  });

  it('sets getFeatureDispatch props to trigger desired action', () => {
    expect(result.getFeatureDispatch).toBeInstanceOf(Function);
  });
  it('sets getFeatureCodeDispatch props to trigger desired action', () => {
    expect(result.getFeatureCodeDispatch).toBeInstanceOf(Function);
  });
});
