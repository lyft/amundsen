// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as DocumentTitle from 'react-document-title';

import TagsListContainer from 'components/Tags';

import { BROWSE_PAGE_DOCUMENT_TITLE } from './constants';

import './styles.scss';

export class BrowsePage extends React.Component {
  render() {
    return (
      /* TODO: add expand/collapse behavior */
      <DocumentTitle title={BROWSE_PAGE_DOCUMENT_TITLE}>
        <main className="container">
          <div className="row">
            <div className="col-xs-12 col-md-10 col-md-offset-1">
              <TagsListContainer shortTagsList={false} />
            </div>
          </div>
        </main>
      </DocumentTitle>
    );
  }
}

export default BrowsePage;
