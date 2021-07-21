// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mount } from 'enzyme';

import AvatarLabel from 'components/AvatarLabel';

import { ResourceType } from 'interfaces';

import { OwnerEditor, OwnerEditorProps } from '.';
import * as Constants from './constants';

const setup = (propOverrides?: Partial<OwnerEditorProps>) => {
  const props: OwnerEditorProps = {
    errorText: null,
    isLoading: false,
    itemProps: {},
    isEditing: undefined,
    setEditMode: jest.fn(),
    onUpdateList: jest.fn(),
    readOnly: undefined,
    resourceType: ResourceType.table,
    ...propOverrides,
  };
  // eslint-disable-next-line react/jsx-props-no-spreading
  const wrapper = mount<OwnerEditor>(<OwnerEditor {...props} />);

  return {
    props,
    wrapper,
  };
};

describe('OwnerEditor', () => {
  describe('render', () => {
    describe('when no owners', () => {
      it('renders text if readOnly', () => {
        const { wrapper } = setup({ readOnly: true });
        expect(wrapper.find(AvatarLabel).text()).toContain(
          Constants.NO_OWNER_TEXT
        );
      });

      it('renders add button if not readOnly', () => {
        const { wrapper } = setup();
        expect(wrapper.find('.add-item-button').text()).toContain(
          Constants.ADD_OWNER
        );
      });
    });

    it('renders owners if they exist', () => {
      const { wrapper } = setup({
        itemProps: { owner1: {}, owner2: {}, owner3: {} },
      });
      expect(wrapper.find(AvatarLabel).length).toBe(3);
    });

    describe('editing modal', () => {
      it('renders when not readOnly', () => {
        const { wrapper } = setup();
        expect(wrapper.find('.owner-editor-modal').exists()).toBe(true);
      });

      it('does not render when readOnly', () => {
        const { wrapper } = setup({ readOnly: true });
        expect(wrapper.find('.owner-editor-modal').exists()).toBe(false);
      });
    });
  });
});
