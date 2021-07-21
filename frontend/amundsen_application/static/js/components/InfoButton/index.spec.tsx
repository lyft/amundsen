// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import SanitizedHTML from 'react-sanitized-html';
import { shallow } from 'enzyme';
import { OverlayTrigger, Popover } from 'react-bootstrap';

import InfoButton, { InfoButtonProps } from '.';

describe('InfoButton', () => {
  let props: InfoButtonProps;
  let subject;

  beforeEach(() => {
    props = {
      infoText: 'Some info text to share',
      title: 'Popover Title',
      placement: 'left',
    };
    subject = shallow(<InfoButton {...props} />);
  });

  describe('render', () => {
    it('renders OverlayTrigger w/ correct placement', () => {
      expect(subject.find(OverlayTrigger).props().placement).toEqual(
        props.placement
      );
    });

    it('renders OverlayTrigger w/ correct Popover', () => {
      const expectedPopover = (
        <Popover id="popover-trigger-hover-focus" title={props.title}>
          <SanitizedHTML html={props.infoText} />
        </Popover>
      );
      expect(subject.find(OverlayTrigger).props().overlay).toEqual(
        expectedPopover
      );
    });
  });
});
