// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0
/* eslint-disable no-underscore-dangle */

import { LineageItem } from 'interfaces';
import globalState from 'fixtures/globalState';

import {
  buildEdges,
  buildNodes,
  buildSVG,
  compactLineage,
  decompactLineage,
  generateNodeId,
  generatePath,
  getChildren,
  hasLineageData,
  prepareNodeForRender,
  nodeXFromParents,
  reflowLineage,
  toggler,
} from './chart';

import { TreeLineageItem } from './types';

const item: LineageItem = {
  badges: [],
  cluster: 'cluster',
  database: 'database',
  key: 'h/root',
  level: 0,
  name: 'table',
  parent: null,
  schema: 'schema',
  usage: null,
};

const rootNode = {
  children: undefined,
  data: item as LineageItem & { id?: string; data: TreeLineageItem },
  parent: null,
  x: 100,
  y: 100,
  id: '1',
};

const nodeWithParent = {
  children: undefined,
  data: item as LineageItem & { id?: string; data: TreeLineageItem },
  parent: rootNode,
  x: 100,
  y: 100,
  id: '2',
};

describe('D3 Lineage chart', () => {
  describe('utilities', () => {
    it('node id generation should be consistent', () => {
      expect(generateNodeId(1, 0)).toEqual(1);
      expect(generateNodeId(2, 0)).toEqual(2);
      expect(generateNodeId(1, 1)).toEqual(1001);
      expect(generateNodeId(1, 2)).toEqual(2001);
    });

    it('node path should be using correct coordinates', () => {
      expect(generatePath({ x: 3, y: 5 }, { x: 1, y: 1 })).toMatch(/C 3 3/);
    });

    it("x coords for a child node should be the avg of parents' x", () => {
      expect(nodeXFromParents([{ x: 4 }, { x: 8 }])).toEqual(6);
    });

    it('should be possible to get folded/unfolded children', () => {
      expect(getChildren({ ...item, children: [1] })).toHaveLength(1);
      expect(getChildren({ ...item, _children: [1, 4] })).toHaveLength(2);
      expect(getChildren(item)).toHaveLength(0);
    });

    it('should be possible to verify presence of lineage data', () => {
      expect(
        hasLineageData({ upstream_entities: [], downstream_entities: [] })
      ).toBe(false);
      expect(
        hasLineageData({ upstream_entities: [], downstream_entities: [item] })
      ).toBe(true);
      expect(
        hasLineageData({ upstream_entities: [item], downstream_entities: [] })
      ).toBe(true);
    });

    it('should be possible to prepare coordinates & id', () => {
      const nodeWithId = prepareNodeForRender({ ...rootNode, id: null }, 5);
      expect(nodeWithId.id).toEqual(5);
      expect(nodeWithId.x0).toEqual(100);
      expect(nodeWithId.y0).toEqual(100);

      const anotherNodeWithId = prepareNodeForRender(
        { ...nodeWithId, x: 7 },
        3
      );
      expect(anotherNodeWithId.id).toEqual(5);
      expect(anotherNodeWithId.x0).toEqual(7);
    });
  });

  describe('graph structure', () => {
    it('node with multiple parents should be deduplicated by compact', () => {
      const withMultipleParents: LineageItem[] = [
        item,
        { ...item, key: 'another-parent' },
        { ...item, level: 1, key: 'no-parent-level-1', parent: '' },
        { ...item, key: 'child', parent: 'h/root' },
        { ...item, key: 'child', parent: 'another-parent' },
      ];

      const compacted = compactLineage(withMultipleParents);
      expect(compacted).toHaveLength(4);

      const compactedChild = compacted.find((i) => i.key === 'child');
      expect(compactedChild?._parents).toHaveLength(2);

      const withAddedRootParent = compacted.find(
        (i) => i.key === 'no-parent-level-1'
      );
      expect(withAddedRootParent?.parent).toEqual('h/root');
    });

    it('node with multiple parents should be unfolded # of parents times', () => {
      const withMultipleParents: LineageItem[] = [
        item,
        { ...item, key: 'another-parent' },
        { ...item, key: 'child', parent: 'h/root' },
        { ...item, key: 'child', parent: 'another-parent' },
      ];
      const compacted = compactLineage(withMultipleParents);

      const compactedNodes = compacted.map((i, idx) => ({
        ...i,
        id: idx,
        data: { data: { key: i.key, _parents: i._parents } },
        y: 100,
        x: 100,
      }));

      const decompactedNodes = decompactLineage(compactedNodes);
      expect(decompactedNodes).toHaveLength(4);
    });

    it('should swap parent -> child to child -> parent relationship', () => {
      const upstreamLineage = [
        item,
        ...globalState.lineage.lineageTree.upstream_entities,
      ];

      const invertedLineage = reflowLineage(upstreamLineage);
      const parentOne = invertedLineage.find((n) => n.key === 'h/parent-1');
      const parentTwoSolo = invertedLineage.find(
        (n) => n.key === 'h/parent-2-solo'
      );
      const parentThree = invertedLineage.find((n) => n.key === 'h/parent-3');
      expect(invertedLineage).toHaveLength(6);
      expect(parentOne?.parent).toEqual('h/root');
      expect(parentTwoSolo?.parent).toEqual('h/parent-1');
      expect(parentThree?.parent).toEqual('h/parent-2');
    });
  });

  describe('render', () => {
    it('should render an svg', () => {
      const el = document.createElement('div');
      buildSVG(el, { height: 100, width: 100 });
      expect(el.getElementsByTagName('svg').length).toBe(1);
      expect(el.getElementsByTagName('g').length).toBe(1);
    });

    it('click on a root behaves as expected', () => {
      const clickSpy = jest.fn();
      const onClickRoot = toggler(clickSpy);
      onClickRoot(rootNode, [rootNode, nodeWithParent, rootNode]);
      expect(clickSpy.mock.calls.length).toBe(2);
      expect(clickSpy.mock.calls[0][0]).toBe(rootNode);

      const onClickNode = toggler(clickSpy);
      onClickNode(nodeWithParent, [rootNode, nodeWithParent]);
      expect(clickSpy.mock.calls.length).toBe(2);
      expect(clickSpy.mock.calls[1][0]).toBe(rootNode);
    });

    it('should not error out on building nodes and edges', () => {
      const el = document.createElement('div');
      const { g } = buildSVG(el, { height: 100, width: 100 });
      const edges = [nodeWithParent];
      const clickSpy = jest.fn();
      const onClickRoot = toggler(clickSpy);

      // Not sure how this could be tested.
      buildEdges(g, rootNode, edges);
      buildNodes(g, rootNode, edges, onClickRoot);
    });
  });
});
