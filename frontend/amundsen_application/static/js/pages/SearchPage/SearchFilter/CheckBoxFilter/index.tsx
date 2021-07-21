// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import { GlobalState } from 'ducks/rootReducer';
import {
  updateFilterByCategory,
  UpdateFilterRequest,
  FilterOptions,
} from 'ducks/search/filters/reducer';

import CheckBoxItem from 'components/Inputs/CheckBoxItem';

export interface CheckboxFilterProperties {
  label: string;
  value: string;
}

interface OwnProps {
  categoryId: string;
  checkboxProperties: CheckboxFilterProperties[];
}

interface StateFromProps {
  checkedValues: FilterOptions;
}

interface DispatchFromProps {
  updateFilter: (
    categoryId: string,
    checkedValues: FilterOptions | undefined
  ) => UpdateFilterRequest;
}

export type CheckBoxFilterProps = OwnProps & DispatchFromProps & StateFromProps;

export class CheckBoxFilter extends React.Component<CheckBoxFilterProps> {
  createCheckBoxItem = (
    categoryId: string,
    key: string,
    item: CheckboxFilterProperties
  ) => {
    const { label, value } = item;
    return (
      <CheckBoxItem
        key={key}
        checked={this.props.checkedValues[value]}
        name={categoryId}
        value={value}
        onChange={this.onCheckboxChange}
      >
        <span className="subtitle-2">{label}</span>
      </CheckBoxItem>
    );
  };

  onCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let { checkedValues } = this.props;
    const { value } = e.target;
    const categoryId = e.target.name;

    if (e.target.checked) {
      checkedValues = {
        ...this.props.checkedValues,
        [value]: true,
      };
    } else {
      /* Removing an object key with object destructuring */
      const {
        [value]: removed,
        ...newCheckedValues
      } = this.props.checkedValues;
      checkedValues = newCheckedValues;
    }

    if (Object.keys(checkedValues).length === 0) {
      this.props.updateFilter(categoryId, undefined);
    } else {
      this.props.updateFilter(categoryId, checkedValues);
    }
  };

  render = () => {
    const { categoryId, checkboxProperties } = this.props;
    return (
      <div className="checkbox-section-content">
        {checkboxProperties.map((item, index) =>
          this.createCheckBoxItem(
            categoryId,
            `item:${categoryId}:${index}`,
            item
          )
        )}
      </div>
    );
  };
}

export const mapStateToProps = (state: GlobalState, ownProps: OwnProps) => {
  const filterState = state.search.filters;
  let filterValues = filterState[state.search.resource]
    ? filterState[state.search.resource][ownProps.categoryId]
    : {};
  if (!filterValues) {
    filterValues = {};
  }

  return {
    checkedValues: filterValues,
  };
};

export const mapDispatchToProps = (dispatch: any) =>
  bindActionCreators(
    {
      updateFilter: (
        categoryId: string,
        checkedValues: FilterOptions | undefined
      ) => updateFilterByCategory({ categoryId, value: checkedValues }),
    },
    dispatch
  );

export default connect<StateFromProps, DispatchFromProps, OwnProps>(
  mapStateToProps,
  mapDispatchToProps
)(CheckBoxFilter);
