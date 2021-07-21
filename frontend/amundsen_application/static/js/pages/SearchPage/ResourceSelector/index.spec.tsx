// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mocked } from 'ts-jest/utils';
import { shallow } from 'enzyme';

import globalState from 'fixtures/globalState';
import { ResourceType } from 'interfaces/Resources';
import {
  getDisplayNameByResource,
  indexDashboardsEnabled,
  indexFeaturesEnabled,
  indexUsersEnabled,
} from 'config/config-utils';
import {
  mapDispatchToProps,
  mapStateToProps,
  ResourceSelector,
  ResourceSelectorProps,
} from '.';

jest.mock('config/config-utils', () => ({
  getDisplayNameByResource: jest.fn(() => 'Resource'),
  indexUsersEnabled: jest.fn(),
  indexFeaturesEnabled: jest.fn(),
  indexDashboardsEnabled: jest.fn(),
}));

describe('ResourceSelector', () => {
  const setup = (propOverrides?: Partial<ResourceSelectorProps>) => {
    const props = {
      resource: ResourceType.table,
      tables: globalState.search.tables,
      users: globalState.search.users,
      dashboards: globalState.search.dashboards,
      features: globalState.search.features,
      setResource: jest.fn(),
      ...propOverrides,
    };
    const wrapper = shallow<ResourceSelector>(<ResourceSelector {...props} />);
    return { props, wrapper };
  };

  describe('renderRadioOption', () => {
    const { wrapper, props } = setup();
    const instance = wrapper.instance();
    const radioConfig = {
      type: ResourceType.table,
      label: getDisplayNameByResource(ResourceType.table),
      count: 10,
    };
    const content = shallow(instance.renderRadioOption(radioConfig, 0));

    it('renders an input with correct properties', () => {
      const inputProps = content.find('input').props();
      expect(inputProps.type).toEqual('radio');
      expect(inputProps.name).toEqual('resource');
      expect(inputProps.value).toEqual(radioConfig.type);
      expect(inputProps.checked).toEqual(props.resource === radioConfig.type);
      expect(inputProps.onChange).toEqual(instance.onChange);
    });

    it('renders with the correct labels', () => {
      expect(content.text()).toEqual(
        `${radioConfig.label}${radioConfig.count}`
      );
    });
  });

  describe('onChange', () => {
    it('calls setResource with the appropriate resource type', () => {
      const mockEvent = {
        target: {
          value: ResourceType.table,
        },
      };
      const { wrapper, props } = setup();
      const setResourceSpy = jest.spyOn(props, 'setResource');
      wrapper.instance().onChange(mockEvent);
      expect(setResourceSpy).toHaveBeenCalledWith(mockEvent.target.value);
    });
  });

  describe('render', () => {
    let props;
    let wrapper;

    let dashboardOptionConfig;
    let featureOptionConfig;
    let tableOptionConfig;
    let userOptionConfig;
    let renderRadioOptionSpy;

    beforeAll(() => {
      const setupResult = setup();
      props = setupResult.props;
      wrapper = setupResult.wrapper;

      dashboardOptionConfig = {
        type: ResourceType.dashboard,
        label: getDisplayNameByResource(ResourceType.dashboard),
        count: props.dashboards.total_results,
      };
      featureOptionConfig = {
        type: ResourceType.feature,
        label: getDisplayNameByResource(ResourceType.feature),
        count: props.features.total_results,
      };
      tableOptionConfig = {
        type: ResourceType.table,
        label: getDisplayNameByResource(ResourceType.table),
        count: props.tables.total_results,
      };
      userOptionConfig = {
        type: ResourceType.user,
        label: getDisplayNameByResource(ResourceType.user),
        count: props.users.total_results,
      };

      renderRadioOptionSpy = jest.spyOn(
        wrapper.instance(),
        'renderRadioOption'
      );
    });

    it('renders the table resource option', () => {
      renderRadioOptionSpy.mockClear();
      wrapper.instance().render();
      expect(renderRadioOptionSpy).toHaveBeenCalledWith(tableOptionConfig, 0);
    });

    describe('user resource', () => {
      it('renders when enabled', () => {
        mocked(indexUsersEnabled).mockImplementationOnce(() => true);
        renderRadioOptionSpy.mockClear();
        wrapper.instance().render();
        expect(renderRadioOptionSpy).toHaveBeenCalledWith(userOptionConfig, 1);
      });

      it('does not render when disabled', () => {
        mocked(indexUsersEnabled).mockImplementationOnce(() => false);
        renderRadioOptionSpy.mockClear();
        wrapper.instance().render();
        expect(renderRadioOptionSpy).not.toHaveBeenCalledWith(
          userOptionConfig,
          1
        );
      });
    });

    describe('dashboard resource', () => {
      it('renders when enabled', () => {
        mocked(indexDashboardsEnabled).mockImplementationOnce(() => true);
        renderRadioOptionSpy.mockClear();
        wrapper.instance().render();
        expect(renderRadioOptionSpy).toHaveBeenCalledWith(
          dashboardOptionConfig,
          1
        );
      });

      it('does not render when disabled', () => {
        mocked(indexDashboardsEnabled).mockImplementationOnce(() => false);
        renderRadioOptionSpy.mockClear();
        wrapper.instance().render();
        expect(renderRadioOptionSpy).not.toHaveBeenCalledWith(
          dashboardOptionConfig
        );
      });
    });
  });
});

describe('mapStateToProps', () => {
  let result;

  beforeAll(() => {
    result = mapStateToProps(globalState);
  });

  it('sets resource on the props', () => {
    expect(result.resource).toEqual(globalState.search.resource);
  });

  it('sets tables on the props', () => {
    expect(result.tables).toEqual(globalState.search.tables);
  });

  it('sets users on the props', () => {
    expect(result.users).toEqual(globalState.search.users);
  });

  it('sets dashboards on the props', () => {
    expect(result.dashboards).toEqual(globalState.search.dashboards);
  });
});

describe('mapDispatchToProps', () => {
  let result;
  let dispatch;
  beforeAll(() => {
    dispatch = jest.fn(() => Promise.resolve());
    result = mapDispatchToProps(dispatch);
  });

  it('sets setResource on the props', () => {
    expect(result.setResource).toBeInstanceOf(Function);
  });
});
