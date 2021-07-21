// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { GlobalState } from 'ducks/rootReducer';

import globalState from 'fixtures/globalState';
import { mapDispatchToProps, mapStateToProps } from '.';

describe('mapStateToProps', () => {
  let result;
  let expectedItemProps;
  let mockState: GlobalState;
  beforeAll(() => {
    mockState = {
      ...globalState,
      feature: {
        ...globalState.feature,
        isLoadingOwners: true,
        feature: {
          ...globalState.feature.feature,
          description: 'test description',
        },
      },
    };
  });

  it('returns expected props', () => {
    result = mapStateToProps(mockState);
    expectedItemProps = mockState.feature.feature.description;
    expect(result.refreshValue).toEqual(expectedItemProps);
  });
});

describe('mapDispatchToProps', () => {
  let dispatch;
  let result;
  beforeAll(() => {
    dispatch = jest.fn(() => Promise.resolve());
    result = mapDispatchToProps(dispatch);
  });

  it('sets getLatestValue props to trigger desired action', () => {
    expect(result.getLatestValue).toBeInstanceOf(Function);
  });
  it('sets onSubmitValue props to trigger desired action', () => {
    expect(result.onSubmitValue).toBeInstanceOf(Function);
  });
});
