import { Lineage } from 'interfaces';
import { select } from 'd3-selection';
import chart, { LineageChart } from './chart';
import { Dimensions, Labels } from './types';

const actions = {
  create: (
    el: HTMLElement,
    lineage: Lineage,
    dimensions: Dimensions,
    labels: Labels
  ): LineageChart => {
    const c = chart();
    select(el).datum({ lineage, dimensions, labels }).call(c);

    return c;
  },
  destroy: (el: HTMLElement) => {
    select(el).remove();
  },
};

export default actions;
