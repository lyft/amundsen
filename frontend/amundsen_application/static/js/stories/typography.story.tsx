// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';

import StorySection from '../components/StorySection';

export default {
  title: 'Attributes/Typography',
};

export const TypographyUpdated = () => (
  <>
    <StorySection title="Headlines">
      <>
        <h1 className="text-headline-w1">Heading with .text-headline-w1</h1>
        <h1 className="text-headline-w2">Heading with .text-headline-w2</h1>
        <h1 className="text-headline-w3">Heading with .text-headline-w3</h1>
      </>
    </StorySection>
    <StorySection title="Titles">
      <>
        <h1 className="text-title-w1">Title with .text-title-w1</h1>
        <h1 className="text-title-w2">Title with .text-title-w2</h1>
        <h1 className="text-title-w3">Title with .text-title-w3</h1>
      </>
    </StorySection>
    <StorySection title="Subtitles">
      <>
        <h1 className="text-subtitle-w1">Subtitle with .text-subtitle-w1</h1>
        <h1 className="text-subtitle-w2">Subtitle with .text-subtitle-w2</h1>
        <h1 className="text-subtitle-w3">Subtitle with .text-subtitle-w3</h1>
      </>
    </StorySection>
    <StorySection title="Body Text">
      <>
        <p className="text-body-w1">Subtitle with .text-body-w1</p>
        <p className="text-body-w2">Subtitle with .text-body-w2</p>
        <p className="text-body-w3">Subtitle with .text-body-w3</p>
      </>
    </StorySection>
    <StorySection title="Caption Text">
      <>
        <p className="text-caption-w1">Caption with .text-caption-w1</p>
        <p className="text-caption-w2">Caption with .text-caption-w2</p>
      </>
    </StorySection>
    <StorySection title="Code Text">
      <>
        <p className="text-monospace-w3">Code with .text-monospace-w3</p>
      </>
    </StorySection>
  </>
);

TypographyUpdated.storyName = 'Typography';

export const Typography = () => (
  <>
    <StorySection title="Headings">
      <>
        <h1>Raw h1</h1>
        <h2>Raw h2</h2>
        <h3>Raw h3</h3>
        <h4>Raw h4</h4>
        <h5>Raw h5</h5>
        <h6>Raw h6</h6>
        <hr />
        <h1 className="title-2">Heading with .title-2</h1>
        <h1 className="title-3">Heading with .title-3</h1>
        <h1 className="subtitle-1">Heading with .subtitle-1</h1>
        <h1 className="subtitle-2">Heading with .subtitle-2</h1>
        <h1 className="text-subtitle-w3">Heading with .text-subtitle-w3</h1>
      </>
    </StorySection>
    <StorySection title="Body Text">
      <>
        <p>Raw p</p>
        <hr />
        <p className="body-1">Paragraph with .body-1</p>
        <p className="body-2">Paragraph with .body-2</p>
        <p className="body-3">Paragraph with .body-3</p>
        <p className="body-secondary-3">Paragraph with .body-secondary-3</p>
        <p className="body-placeholder">Paragraph with .body-placeholder</p>
        <p className="body-link">Paragraph with .body-link</p>
        <p className="caption">Paragraph with .caption</p>
        <p className="column-name">Paragraph with .column-name</p>
        <p className="resource-type">Paragraph with .resource-type</p>
        <p className="helper-text">Paragraph with .helper-text</p>
        <p className="text-placeholder">Paragraph with .text-placeholder</p>
        <p className="text-secondary">Paragraph with .text-secondary</p>
        <p className="text-primary">Paragraph with .text-primary</p>
      </>
    </StorySection>
  </>
);

Typography.storyName = 'Deprecated: Headings & Body';
