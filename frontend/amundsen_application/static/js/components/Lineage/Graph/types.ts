import { HierarchyPointNode } from 'd3-hierarchy';
import { LineageItem } from 'interfaces';

export type Coordinates = {
  x: number;
  y: number;
};

export type Dimensions = {
  width: number;
  height: number;
};

export type Labels = {
  upstream: string;
  downstream: string;
};

export type TreeLineageItem = LineageItem & {
  data?: TreeLineageItem;
  _parents: string[];
  id?: string;
};

export type TreeLineageNode = HierarchyPointNode<
  LineageItem & { id?: string; data: TreeLineageItem }
> & { _children?: TreeLineageNode[]; x0?: number; y0?: number; key?: string };
