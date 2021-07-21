export const NO_WATERMARK_LINE_1 = 'Non-Partitioned Table';
export const NO_WATERMARK_LINE_2 = 'Data available for all dates';
export const LOW_WATERMARK_LABEL = 'From:';
export const HIGH_WATERMARK_LABEL = 'To:';
export const WATERMARK_INPUT_FORMAT = 'YYYY-MM-DD';

export enum WatermarkType {
  HIGH = 'high_watermark',
  LOW = 'low_watermark',
}
