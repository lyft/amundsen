// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import * as ReactDOMServer from 'react-dom/server';
import { Lineage } from 'interfaces';
import { LeftArrowIcon, RightArrowIcon } from '../../SVGIcons';
import lineageWrapper from './wrapper';
import { LineageChart } from './chart';
import { CHART_DEFAULT_DIMENSIONS, LINEAGE_SCENE_MARGIN } from './constants';
import './styles.scss';

export interface GraphProps {
  lineage: Lineage;
}

export const getDimensions = ({ width, height }: DOMRect) => ({
  width:
    (width || CHART_DEFAULT_DIMENSIONS.width) -
    (LINEAGE_SCENE_MARGIN.left + LINEAGE_SCENE_MARGIN.right),
  height:
    (height || CHART_DEFAULT_DIMENSIONS.height) -
    (LINEAGE_SCENE_MARGIN.top + LINEAGE_SCENE_MARGIN.bottom),
});

const DOWNSTREAM_ARROW_LABEL = 'Downstream';
const UPSTREAM_ARROW_LABEL = 'Upstream';
const FILL_ARROW_LABEL = '#acacc0';

export const Graph: React.FC<GraphProps> = ({ lineage }: GraphProps) => {
  const rootRef = React.useRef<HTMLDivElement>(null);
  const [scene, setScene] = React.useState<LineageChart | null>(null);

  // Setting up margins & render screen for the graph.
  React.useEffect(() => {
    if (!scene && rootRef.current) {
      const dimensions = getDimensions(rootRef.current.getBoundingClientRect());

      const currentScene = lineageWrapper.create(
        rootRef.current,
        lineage,
        dimensions,
        {
          upstream: `${ReactDOMServer.renderToString(
            <div className="text-title-w2">
              <LeftArrowIcon fill={FILL_ARROW_LABEL} />
              <span>{UPSTREAM_ARROW_LABEL}</span>
            </div>
          )}`,
          downstream: `${ReactDOMServer.renderToString(
            <div className="text-title-w2">
              <RightArrowIcon fill={FILL_ARROW_LABEL} />
              <span>{DOWNSTREAM_ARROW_LABEL}</span>
            </div>
          )}`,
        }
      );

      setScene(() => currentScene);
    }

    return () => {
      if (scene && rootRef && rootRef.current) {
        lineageWrapper.destroy(rootRef.current);
      }
    };
  }, [rootRef, scene]);

  return <div className="lineage-graph" ref={rootRef} />;
};

export default Graph;
