// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import 'components/Inputs/styles.scss';

export interface CheckBoxItemProps {
  checked?: boolean;
  disabled?: boolean;
  name: string;
  onChange: (e: React.FormEvent<HTMLInputElement>) => any;
  value: string;
  children: React.ReactNode;
}

const CheckBoxItem: React.FC<CheckBoxItemProps> = ({
  checked = false,
  disabled = false,
  name,
  onChange,
  value,
  children,
}: CheckBoxItemProps) => (
  <div className="checkbox">
    <label className="checkbox-label">
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        name={name}
        onChange={onChange}
        value={value}
      />
      {children}
    </label>
  </div>
);

export default CheckBoxItem;
