// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mocked } from 'ts-jest/utils';

import { indexUsersEnabled } from 'config/config-utils';

import { GlobalState } from 'ducks/rootReducer';

import globalState from 'fixtures/globalState';
import { activeUser0 } from 'fixtures/metadata/users';
import { mapDispatchToProps, mapStateToProps } from '.';

jest.mock('config/config-utils', () => ({
  indexUsersEnabled: jest.fn(),
}));

describe('mapStateToProps', () => {
  let result;
  let expectedItemProps;
  let mockState: GlobalState;
  beforeAll(() => {
    mockState = {
      ...globalState,
      tableMetadata: {
        ...globalState.tableMetadata,
        tableOwners: {
          owners: {
            [activeUser0.user_id]: activeUser0,
          },
          isLoading: false,
        },
      },
    };
  });

  it('returns expected itemProps when indexUsersEnabled()', () => {
    mocked(indexUsersEnabled).mockImplementation(() => true);
    result = mapStateToProps(mockState);
    const id = activeUser0.user_id;
    expectedItemProps = {
      [id]: {
        label: activeUser0.display_name,
        link: `/user/${id}?source=owned_by`,
        isExternal: false,
      },
    };
    expect(result.itemProps).toEqual(expectedItemProps);
  });

  it('returns expected itemProps when !indexUsersEnabled()', () => {
    mocked(indexUsersEnabled).mockImplementation(() => false);
    result = mapStateToProps(mockState);
    expectedItemProps = {
      [activeUser0.user_id]: {
        label: activeUser0.display_name,
        link: activeUser0.profile_url,
        isExternal: true,
      },
    };
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
