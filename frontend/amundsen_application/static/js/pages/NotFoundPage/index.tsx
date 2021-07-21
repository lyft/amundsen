// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as DocumentTitle from 'react-document-title';

// TODO: Use css-modules instead of 'import'
import './styles.scss';

import Breadcrumb from 'components/Breadcrumb';

const NotFoundPage: React.FC<any> = () => (
  <DocumentTitle title="404 Page Not Found - Amundsen">
    <div className="container not-found-page">
      <Breadcrumb path="/" text="Home" />
      <h1>404 Page Not Found</h1>
      <img className="icon icon-alert" alt="" />
    </div>
  </DocumentTitle>
);

export default NotFoundPage;
