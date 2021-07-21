// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { GlobalState } from 'ducks/rootReducer';

import globalState from 'fixtures/globalState';
import { activeUser0 } from 'fixtures/metadata/users';
import { getOwnerItemPropsFromUsers } from 'utils/ownerUtils';
import { FEATURE_OWNER_SOURCE, mapDispatchToProps, mapStateToProps } from '.';

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
          owners: [activeUser0],
        },
      },
    };
  });

  it('returns expected props', () => {
    result = mapStateToProps(mockState);
    expectedItemProps = getOwnerItemPropsFromUsers(
      mockState.feature.feature.owners,
      FEATURE_OWNER_SOURCE
    );
    expect(result.isLoading).toEqual(mockState.feature.isLoadingOwners);
    expect(result.itemProps).toEqual(expectedItemProps);
  });
});

describe('mapDispatchToProps', () => {
  let dispatch;
  let result;
  beforeAll(() => {
    dispatch = jest.fn(() => Promise.resolve());
    result = mapDispatchToProps(dispatch);
  });

  it('sets onUpdateList props to trigger desired action', () => {
    expect(result.onUpdateList).toBeInstanceOf(Function);
  });
});
