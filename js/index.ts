// Copyright (c) Paddy Mullen
// Distributed under the terms of the Modified BSD License.

import { ColumnsEditor, ColumnsEditorEx } from './components/ColumnsEditor';
import { WidgetDCFCellExample } from './components/DCFCell';
import { DFViewer, DFViewerEx } from './components/DFViewerParts/DFViewer';
import { HistogramCell } from './components/DFViewerParts/HistogramCell';
import { DependentTabs } from './components/DependentTabs';
import { OperationViewer } from './components/Operations';
//import { DFData, DFViewerConfig } from './components/DFViewerParts/DFWhole';
import { StatusBar } from './components/StatusBar';
//import { StatusBarEx } from './components/StatusBar';


export * from './version';
export * from './dcefwidget';
export * as bakedData from './baked_data/staticData';

export const extraComponents = {
  ColumnsEditor,
  DependentTabs,
  OperationViewer,
  WidgetDCFCellExample,
  ColumnsEditorEx,
  DFViewer,
  DFViewerEx,
  StatusBar,
  HistogramCell,
};

