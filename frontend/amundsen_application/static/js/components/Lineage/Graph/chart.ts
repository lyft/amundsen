/* eslint-disable no-underscore-dangle, no-param-reassign */

import {
  hierarchy,
  stratify as d3Stratify,
  tree as d3Tree,
} from 'd3-hierarchy';
import { zoom as d3Zoom, zoomIdentity } from 'd3-zoom';
import { select, Selection } from 'd3-selection';
import { Lineage, LineageItem } from 'interfaces';
import {
  ANIMATION_DURATION,
  CHART_DEFAULT_DIMENSIONS,
  CHART_DEFAULT_LABELS,
  LINEAGE_SCENE_MARGIN,
  NODE_STATUS_Y_OFFSET,
  NODE_LABEL_Y_OFFSET,
  UPSTREAM_LABEL_OFFSET,
} from './constants';
import { Coordinates, Dimensions, Labels, TreeLineageNode } from './types';

export interface LineageChartData {
  lineage: Lineage;
  dimensions: Dimensions;
  labels: Labels;
}

export interface LineageChart {
  (selection: any): any;
}

// We support up to 1000 direct nodes.
const NODE_LIMIT = 1000;
const ROOT_RADIUS = 12;
const NODE_RADIUS = 8;

/**
 * Generates a fixed node ID from original and offset
 */
export const generateNodeId = (originalId: number, offset: number): number =>
  originalId + NODE_LIMIT * offset;

/**
 * Generate a cartesian path between two nodes.
 */
export const generatePath = (src: Coordinates, dst: Coordinates) =>
  // Multiline return for ease of reading
  `M ${src.y} ${src.x}
          C ${(src.y + dst.y) / 2} ${src.x},
            ${(src.y + dst.y) / 2} ${dst.x},
            ${dst.y} ${dst.x}`;

/**
 * Determines X position for a child node based on parents average.
 */
export const nodeXFromParents = (parents) =>
  parents.reduce((sum: number, p) => sum + p.x, 0) / parents.length;

/**
 * Access the open or collapsed children of a node.
 */
export const getChildren = ({
  children,
  _children,
}: LineageItem & { children?: any; _children?: any }) =>
  children || _children || [];

/**
 * Transposes the descendats of a tree across the Y axis.
 */
const transposeTreeY = (t) =>
  t?.descendants().map((n) => {
    // Transpose Y only if not already done.
    if (n.y > 0) {
      n.y *= -1;
    }
    return n;
  });

/**
 * Add x/y origins for a node and generate an ID if one is not already set.
 */
export const prepareNodeForRender = (n, idx): TreeLineageNode => {
  n.x0 = n.x;
  n.y0 = n.y;
  if (!n.id) {
    // @ts-ignore
    n.id = generateNodeId(idx, 0);
  }
  return n;
};

/**
 * Render the upstream/downstream labels on the lineage graph
 */
const renderLabels = (
  svg: Selection<SVGSVGElement, any, null, any>,
  dimensions: Dimensions,
  labels: Labels
) => {
  svg
    .append('foreignObject')
    // @ts-ignore
    .attr('class', 'graph-direction-label  upstream-label')
    .attr(
      'transform',
      `translate(${
        dimensions.width / 2 -
        UPSTREAM_LABEL_OFFSET -
        LINEAGE_SCENE_MARGIN.right
      }, ${LINEAGE_SCENE_MARGIN.top})`
    )
    .html(labels.upstream);

  svg
    .append('foreignObject')
    // @ts-ignore
    .attr('class', 'graph-direction-label downstream-label')
    .attr(
      'transform',
      `translate(${dimensions.width / 2 + LINEAGE_SCENE_MARGIN.left}, ${
        LINEAGE_SCENE_MARGIN.top
      })`
    )
    .html(labels.downstream);
};

/**
 * The rendering approach we currently use is bidirectional:
 * - Two graphs are rendered across the Y axis from a single root.
 *   - For downstream, this flows as is from the API response
 *   - For upstream however, we need to inverse the parent/child
 *   relationships.
 */
export const reflowLineage = (items: LineageItem[]): LineageItem[] => {
  const rootNode = items.find((n) => n.level === 0);

  const lineageByKey = items.reduce(
    (acc, i) => ({
      ...acc,
      [i.key]: i,
    }),
    {}
  );

  return items.reduce((acc, item) => {
    const parentLevel =
      item.parent && lineageByKey[item.parent]
        ? lineageByKey[item.parent].level
        : -1;

    const shouldSwapRelationship = parentLevel > 0 && parentLevel > item.level;

    let itemsToAdd: LineageItem[] = [];
    if (item.level === 0) {
      // Add the root node without further processing
      return [...acc, item];
    }

    if (item.level === 1) {
      // Level 1 nodes have implicit root parent in all cases.
      itemsToAdd = [{ ...item, parent: rootNode?.key } as LineageItem];
    } else if (!shouldSwapRelationship && parentLevel !== -1) {
      itemsToAdd = [item];
    }

    if (shouldSwapRelationship) {
      // If we are here, we need to change the node direction.
      const childToSwitch = item.parent;
      if (childToSwitch) {
        itemsToAdd = [
          ...itemsToAdd,
          {
            ...lineageByKey[childToSwitch],
            parent: item.key,
          },
        ];
      }
    }

    return [...acc, ...itemsToAdd];
  }, [] as LineageItem[]);
};

/**
 * The d3 Hierarchy module renders single parent relationships only.
 * we compact the lineage to merge duplicate nodes before rendering.
 */
export const compactLineage = (
  items: LineageItem[]
): (LineageItem & { _parents: string[] })[] => {
  const rootNode = items.find((n) => n.level === 0);
  return Object.values(
    items.reduce((acc, n) => {
      if (n.level === 1 && !n.parent && rootNode) {
        n.parent = rootNode.key;
      }

      if (acc.hasOwnProperty(n.key)) {
        acc[n.key]._parents.push(n.parent);
      } else {
        acc[n.key] = n;
        acc[n.key]._parents = [n.parent];
      }
      return acc;
    }, {})
  );
};

/**
 * Allows us to unfurl the list of relationships post stratify-ing, so we can
 * still build the custom edges for multiple parents. The d3 hierarchy keeps
 * a reference to all nodes internally, and we need to not break this reference
 * - e.g. adding a new object overlapping with existing node is ok, replacing
 *        an existing node would produce unexpected rendering behaviour
 */
export const decompactLineage = (nodes): TreeLineageNode[] => {
  const uniqueIds: number[] = [];
  return nodes.reduce((acc, n) => {
    if (n.data.data._parents && n.data.data._parents.length > 1) {
      const parents = nodes.filter((p: TreeLineageNode) =>
        n.data.data._parents.includes(p.data.data.key)
      );
      // Determine layout position of the node based on number of parents.
      n.x = nodeXFromParents(parents);

      // Insert nodes while keeping reference to original one
      parents.forEach((p, idx: number) => {
        const id = generateNodeId(n.id, idx);

        // Attach to children if missing from response.
        if (!p._children) {
          if (!Array.isArray(p.children)) {
            // Init if no current children
            p.children = [n];
          } else if (!p.children.map((c) => c.id).includes(n.id)) {
            // Add if not inbetween the children
            p.children.push(n);
          }
        }

        if (!uniqueIds.includes(id)) {
          if (idx === 0) {
            // Add the original
            n.parent = p;
            acc.push(n);
          } else {
            // Add a shadow node
            acc.push({
              ...n,
              id,
              parent: p,
            });
          }
          uniqueIds.push(id);
        }
      });
    } else if (!uniqueIds.includes(n.id)) {
      acc.push(n);
      uniqueIds.push(n.id);
    }
    return acc;
  }, [] as TreeLineageNode[]);
};

/**
 * Render all edges between connected nodes and seed animations.
 */
export const buildEdges = (g, targetNode, nodes) => {
  const treeSelection = g
    .selectAll('path.graph-link')
    .data(nodes, ({ id }) => id);

  // Enter any new links at the parent's previous position.
  const edgeEnter = treeSelection
    .enter()
    .insert('path', 'g')
    .attr('class', 'graph-link')
    .attr('d', () => {
      const o = { x: targetNode.x0 || 0, y: targetNode.y0 || 0 };
      return generatePath(o, o);
    });

  // Render connection
  edgeEnter
    .merge(treeSelection)
    .transition()
    .duration(ANIMATION_DURATION)
    .attr('d', (d) => generatePath(d, d.parent));

  // Render multiparent connections
  // Transition out on exit.
  treeSelection
    .exit()
    .transition()
    .duration(ANIMATION_DURATION)
    .attr('d', () => {
      const o = { x: targetNode.x, y: targetNode.y };
      return generatePath(o, o);
    })
    .remove();
};

/**
 * Render all nodes and setup transitions as required
 */
export const buildNodes = (g, targetNode, nodes, onClick) => {
  const nodeSelection = g
    .selectAll('g.graph-node')
    // eslint-disable-next-line no-return-assign
    .data(nodes, ({ id }) => id);

  // Toggle children on click.
  // Enter any new modes at the parent's previous position.
  const nodeEnter = nodeSelection
    .enter()
    .append('g')
    .attr('class', 'graph-node')
    .attr('transform', () => `translate(${targetNode.y0},${targetNode.x0})`)
    .on('click', (_, clicked) => onClick(clicked, nodes));

  // Draw circle around the nodes
  nodeEnter.append('circle').attr('class', 'graph-node').attr('r', 0);

  // Position node label
  nodeEnter
    .append('text')
    .attr('dy', NODE_LABEL_Y_OFFSET)
    .attr('text-anchor', 'middle')
    .text((d, idx) => (idx !== 0 && d.data.data.name ? d.data.data.name : ''));

  // Position visual state for for fold/unfold
  nodeEnter
    .append('text')
    .attr('dy', NODE_STATUS_Y_OFFSET)
    .attr('class', 'plus')
    .attr('text-anchor', 'middle');

  const nodeUpdate = nodeEnter.merge(nodeSelection);

  // Transition to the proper position for the node
  nodeUpdate
    .transition()
    .duration(ANIMATION_DURATION)
    .attr('transform', (d) => {
      // DO NOT UPDATE THE POSITION OF ROOT NODE
      if (d.parent === null) {
        d.y = targetNode.y0;
        d.x = targetNode.x0;
      }
      return 'translate(' + d.y + ',' + d.x + ')';
    });

  // Update the node attributes and style
  nodeUpdate
    .select('circle.graph-node')
    .attr('r', ({ depth }) => (depth === 0 ? ROOT_RADIUS : NODE_RADIUS))
    .attr('cursor', 'pointer');

  nodeUpdate.select('text.plus').text((n: TreeLineageNode) => {
    let nodeActionLabel = '';
    if (n.children) {
      nodeActionLabel = '-';
    } else if (n._children) {
      nodeActionLabel = '+';
    }
    return nodeActionLabel;
  });

  // Remove any exiting nodes
  const nodeExit = nodeSelection
    .exit()
    .transition()
    .duration(ANIMATION_DURATION)
    .attr('transform', () => `translate(${targetNode.y},${targetNode.x})`)
    .remove();

  // On exit reduce the node circles size to 0
  nodeExit.select('circle').attr('r', 1e-6);

  // On exit reduce the opacity of text labels
  nodeExit.select('text').style('fill-opacity', 1e-6);
};

/**
 * Creates the d3 tree hierarchy from lineage items.
 */
const buildTree = (treemap, stratify, lineage: LineageItem[]) =>
  Array.isArray(lineage) && lineage.length > 0
    ? treemap(hierarchy(stratify(lineage), ({ children }) => children))
    : null;

/**
 * Create a toggler function with a render callback
 */
export const toggler = (renderer) => (target, nodes) => {
  let roots = nodes.filter((n) => n.parent === null);
  let toUpdate: TreeLineageNode[] = [];
  if (target.parent) {
    if (target.children || target._children) {
      toUpdate = [
        target,
        ...nodes.filter((n) => {
          const targetChildren = getChildren(target);
          const children = getChildren(n);
          return (
            target.id !== n.id &&
            children &&
            children.some((c) =>
              targetChildren.find((tc) => c.data.id === tc.data.id)
            )
          );
        }),
      ];
    } else {
      roots = [];
    }
  } else {
    toUpdate = roots;
  }

  toUpdate.map((n: TreeLineageNode) => {
    if (n.children) {
      n._children = n.children;
      n.children = undefined;
    } else {
      n.children = n._children;
      n._children = undefined;
    }
    return false;
  });

  return roots.map((r: TreeLineageNode) => renderer(r));
};

/**
 * Confirm presence of nodes to render.
 */
export const hasLineageData = (lineage: Lineage) =>
  lineage.downstream_entities.length > 0 ||
  lineage.upstream_entities.length > 0;

/**
 * Get the hierarchy without the two root nodes (upstream and downstream)
 */
export const removeRoots = (nodes) => nodes.filter(({ depth }) => depth !== 0);

/**
 * Builds an svg out of an element
 */
export const buildSVG = (el: HTMLElement, dimensions: Dimensions) => {
  const svg = select(el)
    .append('svg')
    .classed('svg-content', true)
    .attr('width', dimensions.width)
    .attr('height', dimensions.height);

  const g = svg
    .append('g')
    .attr('transform', `translate(${dimensions.width / 2})`);
  return { svg, g };
};

const lc = (): LineageChart => {
  let svg: Selection<SVGSVGElement, any, null, any>;
  let g;

  let dimensions: Dimensions = CHART_DEFAULT_DIMENSIONS;
  let labels: Labels = CHART_DEFAULT_LABELS;
  let lineage: Lineage;

  function renderGraph() {
    const stratify = d3Stratify()
      .id(({ key }: TreeLineageNode) => key)
      .parentId(({ parent }) => parent);

    // Create the treemaps only once per graph and then internally maintain them.
    const treemap = d3Tree().size([
      dimensions.height,
      (dimensions.width -
        (LINEAGE_SCENE_MARGIN.left + LINEAGE_SCENE_MARGIN.right)) /
        2,
    ]);

    const upstreamTree = buildTree(
      treemap,
      stratify,
      lineage.upstream_entities
    );
    const downstreamTree = buildTree(
      treemap,
      stratify,
      lineage.downstream_entities
    );

    // jsdom does not support SVGAnimation, to test rendering
    // disable if running inside jest.
    if (
      typeof navigator.userAgent !== 'string' ||
      !navigator.userAgent.includes('jsdom')
    ) {
      const zoom = d3Zoom().on('zoom', (e) => {
        const { transform } = e;
        // By default make sure to place the graph in center
        if (!e.sourceEvent) {
          transform.x = dimensions.width / 2;
        }

        g.attr('transform', transform);
        // This is awkward, defined as css/js var.
        g.style('stroke-width', 3 / Math.sqrt(transform.k));
      });
      svg.call(zoom).call(zoom.transform, zoomIdentity);
    }

    function renderRelativeTo(targetPosition: TreeLineageNode) {
      // Transpose upstream over Y axis
      const upstreamNodes = transposeTreeY(upstreamTree) || [];

      const downstreamNodes = downstreamTree?.descendants() || [];

      const nodes = upstreamNodes
        .concat(downstreamNodes)
        .map(prepareNodeForRender);
      const nodesToRender = decompactLineage(nodes as TreeLineageNode[]);
      buildNodes(g, targetPosition, nodesToRender, toggler(renderRelativeTo));
      buildEdges(g, targetPosition, removeRoots(nodesToRender));
    }

    renderRelativeTo({
      x0: dimensions.height / 2,
      y0: 0,
    } as TreeLineageNode);
  }

  const chart = ((
    _selection: Selection<HTMLElement, LineageChartData, any, any>
  ) => {
    _selection.each(function bc(_data: LineageChartData) {
      ({ dimensions, labels, lineage } = _data);

      if (!svg) {
        ({ svg, g } = buildSVG(this, dimensions));
      }

      renderLabels(svg, dimensions, labels);

      if (hasLineageData(lineage)) {
        lineage = {
          upstream_entities: compactLineage(
            reflowLineage(lineage.upstream_entities)
          ),
          downstream_entities: compactLineage(lineage.downstream_entities),
        };
        renderGraph();
      }
    });
  }) as LineageChart;

  return chart;
};

export default lc;
