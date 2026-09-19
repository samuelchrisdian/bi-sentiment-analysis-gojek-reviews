/* Registrasi selektif — hanya modul yang benar-benar dipakai, supaya bundel
   produksi tidak memuat seluruh ECharts. */
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart, LineChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
  MarkAreaComponent,
  AxisPointerComponent,
  DatasetComponent,
} from "echarts/components";

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
  MarkAreaComponent,
  AxisPointerComponent,
  DatasetComponent,
]);

export { default as VChart } from "vue-echarts";
