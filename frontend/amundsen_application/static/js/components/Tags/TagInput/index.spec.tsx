// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import { shallow } from 'enzyme';

import { GlobalState } from 'ducks/rootReducer';
import globalState from 'fixtures/globalState';
import { ResourceType } from 'interfaces/Resources';
import {
  TagInput,
  mapDispatchToProps,
  mapStateToProps,
  TagInputProps,
} from '.';

const setup = (propOverrides?: Partial<TagInputProps>) => {
  const props = {
    resourceType: ResourceType.table,
    uriKey: 'test_key',
    updateTags: jest.fn(),
    getAllTags: jest.fn(),
    ...propOverrides,
  };
  const wrapper = shallow<typeof TagInput>(<TagInput {...props} />);
  return { props, wrapper };
};

// TODO - expand test coverage of component class
describe('TagInput', () => {
  it('renders without error', () => {
    expect(() => {
      setup();
    }).not.toThrow();
  });
});

describe('mapStateToProps', () => {
  let result;
  let expectedProps;
  let mockState: GlobalState;
  beforeAll(() => {
    mockState = {
      ...globalState,
    };
  });

  it('returns expected props', () => {
    result = mapStateToProps(mockState);
    expectedProps = {
      allTags: mockState.tags.allTags.tags,
      isLoading:
        mockState.tags.allTags.isLoading ||
        mockState.tags.resourceTags.isLoading,
      tags: mockState.tags.resourceTags.tags,
    };
    expect(result.allTags).toEqual(expectedProps.allTags);
    expect(result.isLoading).toEqual(expectedProps.isLoading);
    expect(result.tags).toEqual(expectedProps.tags);
  });
});

describe('mapDispatchToProps', () => {
  let dispatch;
  let ownProps;
  let result;
  beforeAll(() => {
    dispatch = jest.fn(() => Promise.resolve());
    ownProps = {
      resourceType: ResourceType.table,
      uriKey: 'test_key',
    };
    result = mapDispatchToProps(dispatch, ownProps);
  });

  it('sets getAllTags props to trigger desired action', () => {
    expect(result.getAllTags).toBeInstanceOf(Function);
  });

  it('sets updateTags props to trigger desired action', () => {
    expect(result.updateTags).toBeInstanceOf(Function);
  });
});
