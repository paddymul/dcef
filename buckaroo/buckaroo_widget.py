#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Paddy Mullen.
# Distributed under the terms of the Modified BSD License.

"""
TODO: Add module docstring
"""

from ipywidgets import DOMWidget
import pandas as pd
from traitlets import Unicode, List, Dict, observe

from ._frontend import module_name, module_version


from .customizations.analysis import (TypingStats, ComputedDefaultSummaryStats, DefaultSummaryStats)
from .customizations.histogram import (Histogram)
from .customizations.pd_autoclean_conf import (CleaningConf, NoCleaningConf)
from .customizations.styling import (DefaultSummaryStatsStyling, DefaultMainStyling)
from .pluggable_analysis_framework.analysis_management import DfStats
from .pluggable_analysis_framework.pluggable_analysis_framework import ColAnalysis

from .serialization_utils import EMPTY_DF_WHOLE, check_and_fix_df, pd_to_obj
from .dataflow.dataflow import CustomizableDataflow, StylingAnalysis
from .dataflow.dataflow_extras import (Sampling, exception_protect)
from .dataflow.autocleaning import PandasAutocleaning


class BuckarooProjectWidget(DOMWidget):
    """
    Repetitious code needed to make Jupyter communicate properly with any BuckarooWidget in this package
    
    """
    _model_module = Unicode(module_name).tag(sync=True)
    _view_module  = Unicode(module_name).tag(sync=True)

    _model_module_version = Unicode(module_version).tag(sync=True)
    _view_module_version  = Unicode(module_version).tag(sync=True)



class PdSampling(Sampling):
    @classmethod
    def pre_stats_sample(kls, df):
        # this is a bad place for fixing the dataframe, but for now
        # it's expedient. There probably should be a nother processing
        # step
        df = check_and_fix_df(df)
        if len(df.columns) > kls.max_columns:
            print("Removing excess columns, found %d columns" %  len(df.columns))
            df = df[df.columns[:kls.max_columns]]
        if kls.pre_limit and len(df) > kls.pre_limit:
            sampled = df.sample(kls.pre_limit)
            if isinstance(sampled, pd.DataFrame):
                return sampled.sort_index()
            return sampled
        return df
    pre_limit = 1_000_000


def sym(name):
    return {'symbol':name}

symDf = SymbolDf = {'symbol': 'df'}
class BuckarooWidget(CustomizableDataflow, BuckarooProjectWidget):
    """Extends CustomizableDataFlow and DOMWIdget

    Replaces generic options in CustomizableDataFlow with Pandas implementations
    Also adds buckaroo_state object and communication to simpler CustomizableDataFlow implementations
    
    """

    #### DOMWidget Boilerplate
    _model_name = Unicode('DCEFWidgetModel').tag(sync=True)
    _view_name = Unicode('DCEFWidgetView').tag(sync=True)
    #END DOMWidget Boilerplate

    sampling_klass = PdSampling
    autocleaning_klass = PandasAutocleaning #override the base CustomizableDataFlow klass
    DFStatsClass = DfStats # Pandas Specific
    autoclean_conf = tuple([CleaningConf, NoCleaningConf]) #override the base CustomizableDataFlow conf

    operation_results = Dict(
        {'transformed_df': EMPTY_DF_WHOLE, 'generated_py_code':'# instantiation, unused'}
    ).tag(sync=True)

    df_meta = Dict({
        'columns': 5, # dummy data
        'rows_shown': 20,
        'total_rows': 877}).tag(sync=True)


    buckaroo_state = Dict({
        'cleaning_method': 'NoCleaning',
        'post_processing': '',
        'sampled': False,
        'show_commands': False,
        'df_display': 'main',
        'search_string': '',
        'quick_command_args': {}
    }).tag(sync=True)


    @observe('buckaroo_state')
    @exception_protect('buckaroo_state-protector')
    def _buckaroo_state(self, change):
        #how to control ordering of column_config???
        # dfviewer_config = self._get_dfviewer_config(self.merged_sd, self.style_method)
        # self.widget_args_tuple = [self.processed_df, self.merged_sd, dfviewer_config]
        old, new = change['old'], change['new']
        if not old['post_processing'] == new['post_processing']: 
            self.post_processing_method = new['post_processing']
        if not old['quick_command_args'] == new['quick_command_args']: 
            self.quick_command_args = new['quick_command_args']


        
    #widget config.  Change these via inheritance to alter core behaviors of buckaroo
    #command_klasses = DefaultCommandKlsList
    analysis_klasses = [TypingStats, DefaultSummaryStats,
                        Histogram,
                        ComputedDefaultSummaryStats,
                        StylingAnalysis,
                        DefaultSummaryStats,
                        DefaultSummaryStatsStyling, DefaultMainStyling]



    def add_analysis(self, analysis_klass):
        """
        same as get_summary_sd, call whatever to set summary_sd and trigger further comps
        """

        stats = self.DFStatsClass(
            self.processed_df,
            self.analysis_klasses,
            self.df_name, debug=self.debug)
        stats.add_analysis(analysis_klass)
        self.analysis_klasses = stats.ap.ordered_a_objs
        self.setup_options_from_analysis()
        self.summary_sd = stats.sdf

    def add_processing(self, df_processing_func):
        proc_func_name = df_processing_func.__name__
        class DecoratedProcessing(ColAnalysis):
            provides_defaults = {}
            @classmethod
            def post_process_df(kls, df):
                new_df = df_processing_func(df)
                return [new_df, {}]
            post_processing_method = proc_func_name
        self.add_analysis(DecoratedProcessing)
        temp_buckaroo_state = self.buckaroo_state.copy()
        temp_buckaroo_state['post_processing'] = proc_func_name
        self.buckaroo_state = temp_buckaroo_state


class RawDFViewerWidget(BuckarooProjectWidget):
    """

    A very raw way of instaniating just the DFViewer, not meant for use by enduers

    instead use DFViewer, or PolarsDFViewer which have better convience methods
    """

    #### DOMWidget Boilerplate
    # _model_name = Unicode('InfiniteViewerModel').tag(sync=True)
    # _view_name = Unicode('InfiniteViewerView').tag(sync=True)
    _model_name = Unicode('DFViewerModel').tag(sync=True)
    _view_name = Unicode('DFViewerView').tag(sync=True)
    #_model_id =  Unicode('paddy').tag(sync=True)
    #END DOMWidget Boilerplate

    def __init__(self, df):
        super().__init__()
        print("RawDFViewerWidget 177")
        self.df = df

    payloadArgs = Dict({'sourceName':'paddy', 'start':0, 'end':50}).tag(sync=True)
    payloadResponse = Dict({'key': {'sourceName':'paddy', 'start':0, 'end':49},
                            'data': []}
                            ).tag(sync=True)

    #    @exception_protect('payloadArgsHandler')    
    @observe('payloadArgs')

    def _payloadArgsHandler(self, change):
        start, end = self.payloadArgs['start'], self.payloadArgs['end']
        print(self.payloadArgs)
        if self.payloadArgs.get('sort'):
            sort_dir = self.payloadArgs.get('sort_direction')
            ascending = sort_dir == 'asc'
            slice_df = pd_to_obj(df.sort_values(by=[self.payloadArgs.get('sort')], ascending=ascending)[start:end])
        else:
            slice_df = pd_to_obj(self.df[start:end])
        self.payloadResponse = {'key':self.payloadArgs, 'data':slice_df}


"""
interface PayloadArgs {
    sourceName: string;
    start: number;
    end: number
}
interface PayloadResponse {
    key: PayloadArgs;
    data: DFData;
}
"""

class InfiniteViewerWidget(BuckarooProjectWidget):
    """

    A very raw way of instaniating just the DFViewer, not meant for use by enduers

    instead use DFViewer, or PolarsDFViewer which have better convience methods
    """

    #### DOMWidget Boilerplate
    # _model_name = Unicode('InfiniteViewerModel').tag(sync=True)
    # _view_name = Unicode('InfiniteViewerView').tag(sync=True)
    _model_name = Unicode('InfiniteViewerModel').tag(sync=True)
    _view_name = Unicode('InfiniteViewerView').tag(sync=True)
    #END DOMWidget Boilerplate


    def __init__(self, df):
        super().__init__()
        print("InfiniteViewerWidget 231")
        self.df = df

    payloadArgs = Dict({'sourceName':'paddy', 'start':0, 'end':50}).tag(sync=True)
    payloadResponse = Dict({'key': {'sourceName':'paddy', 'start':0, 'end':49},
                            'data': []}
                            ).tag(sync=True)

    #    @exception_protect('payloadArgsHandler')    
    @observe('payloadArgs')
    def _payloadArgsHandler(self, change):
        start, end = self.payloadArgs['start'], self.payloadArgs['end']
        print(self.payloadArgs)
        if self.payloadArgs.get('sort'):
            sort_dir = self.payloadArgs.get('sort_direction')
            ascending = sort_dir == 'asc'
            slice_df = pd_to_obj(self.df.sort_values(by=[self.payloadArgs.get('sort')], ascending=ascending)[start:end])
        else:
            slice_df = pd_to_obj(self.df[start:end])
        self.payloadResponse = {'key':self.payloadArgs, 'data':slice_df}

