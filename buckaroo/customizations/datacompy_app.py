import pandas as pd
import datacompy

from buckaroo.pluggable_analysis_framework.pluggable_analysis_framework import ColAnalysis
from buckaroo import BuckarooWidget
from buckaroo.dataflow.dataflow_extras import (
    merge_sds, exception_protect)
from traitlets import observe


def col_join_dfs(df1, df2, cmp):
    df1_name = cmp.df1_name
    df2_name = cmp.df2_name

    col_order = df1.columns.to_list()
    for col in df2.columns:
        if col in col_order:
            continue
            
        col_order.append(col)
    eqs = {}
    def get_col_stat(col_name):
        for obj in cmp.column_stats:
            if obj['column'] == col_name:
                return obj
        return None
            
    for col in col_order:
        col_stat = get_col_stat(col)
        if col_stat:
            eqs[col] = {'unequality': col_stat['unequal_cnt']}
        else:
            if col in df1.columns:
                eqs[col] = {'unequality': df1_name}
            else:
                eqs[col] = {'unequality': df2_name}
    ret_df_columns = {}
    column_config_overrides = {}

    for col in col_order:
        eq_col = eqs[col]['unequality']
        if eq_col == df1_name:
            #it's only in df1
            ret_df_columns[col] = df1[col]
        elif eq_col == df2_name:
            #it's only in df2
            ret_df_columns[col] = df2[col]
        elif eq_col == 0:
            #columns are exactly the same
            ret_df_columns[col] = df1[col]
        else:
            ret_df_columns[col] = df1[col]
            #|df2 is a magic value, not a super fan, but it's also unlikely
            df2_col_name = col+"|df2"
            print("col", col, "df2_cols", df2.columns)
            ret_df_columns[df2_col_name] = df2[col]
            
            column_config_overrides[df2_col_name] = {'merge_rule': 'hidden'}
    ret_df = pd.DataFrame(ret_df_columns)
    return ret_df, column_config_overrides, eqs

def DatacompyBuckaroo(df1, df2):
    cmp = datacompy.Compare(
        df1, df2,
        join_columns='A',  # Column to join DataFrames on
        abs_tol=0,  # Absolute tolerance
        rel_tol=0)  # Relative tolerance
    
    def get_df_header(cmp):
        df_header = pd.DataFrame({        
            "DataFrame": [cmp.df1_name, cmp.df2_name],
            "Columns": [cmp.df1.shape[1], cmp.df2.shape[1]],
            "Rows": [cmp.df1.shape[0], cmp.df2.shape[0]]}) #, columns=[0, 1])
        return df_header.T
    
    def column_summary(cmp):
        df1_name = cmp.df1_name
        df2_name = cmp.df2_name
        col_df = pd.DataFrame({
            "Columns in common":[len(cmp.intersect_columns())],
            f"Columns in {df1_name} not in {df2_name}":[ cmp.df1_unq_columns().items],
            f"Columns in {df2_name} not in {df1_name}":[ cmp.df2_unq_columns().items]})
        return col_df.T
    
    def row_summary(cmp):
        # write pad arr function to pad array to number of join columns
        match_criteria = "index"
        if not cmp.on_index:
            match_criteria = ", ".join(cmp.join_columns)
            has_dupes = cmp._any_dupes
            df1_name = cmp.df1_name
            df2_name = cmp.df2_name
    
        row_df = pd.DataFrame({
            "Matched On": [match_criteria],
            "Any Duplicates on match values": [has_dupes],
            "Number of rows in common": cmp.intersect_rows.shape[0],
            f"Number of rows in {df1_name} but not in {df2_name}": cmp.df1_unq_rows.shape[0],
            f"Number of rows in {df2_name} but not in {df1_name}": cmp.df2_unq_rows.shape[0],
            "Number of rows with some compared columns unequal": [cmp.intersect_rows.shape[0] - cmp.count_matching_rows()],
            "Number of rows with all compared columns equal": [cmp.count_matching_rows()]
        })
        return row_df.T
    
    def column_matching(cmp):
        unequal_count = len([col for col in cmp.column_stats if col["unequal_cnt"] > 0])
        equal_count = len([col for col in cmp.column_stats if col["unequal_cnt"] == 0])
        total_unequal_count = sum(col["unequal_cnt"] for col in cmp.column_stats)
    
        col_df = pd.DataFrame({
            "Number of columns compared with some values unequal": [unequal_count],
            "Number of columns with all values equal": [equal_count],
            "Total number of values which compare unequal": [total_unequal_count]})
        return col_df.T
    
    def match_stats(cmp, sample_count=10):
        match_stats = []
        match_sample = []
        any_mismatch = False
        for column in cmp.column_stats:
            if not column["all_match"]:
                any_mismatch = True
                match_stats.append({
                    "Column": column["column"],
                    f"{cmp.df1_name} dtype": column["dtype1"],
                    f"{cmp.df2_name} dtype": column["dtype2"],
                    "# Unequal": column["unequal_cnt"],
                    "Max Diff": column["max_diff"],
                    "# Null Diff": column["null_diff"]})
            if column["unequal_cnt"] > 0:
                match_sample.append(
                    cmp.sample_mismatch(
                        column["column"], sample_count, for_display=True))
    
        df_match_stats = pd.DataFrame(match_stats)
        df_match_stats.sort_values("Column", inplace=True)
        return df_match_stats.T

    class DfHeader(ColAnalysis):
        @classmethod
        def post_process_df(kls, df):
            ab = get_df_header(cmp)
            print("ab", ab)
            return [ab, {}]
        post_processing_method = "Df Headers"


    class ColumnSummary(ColAnalysis):
        @classmethod
        def post_process_df(kls, df):
            col_summary_df = column_summary(cmp)
            print("col_summary", col_summary_df)
            return [col_summary_df, {}]
        post_processing_method = "Column Summary"

    class RowSummary(ColAnalysis):
        @classmethod
        def post_process_df(kls, df):
            return [row_summary(cmp), {}]
        post_processing_method = "Row Summary"

    class ColumnMatching(ColAnalysis):
        @classmethod
        def post_process_df(kls, df):
            return [column_matching(cmp), {}]
        post_processing_method = "Column Matching"

    class MatchStats(ColAnalysis):
        @classmethod
        def post_process_df(kls, df):
            return [match_stats(cmp), {}]
        post_processing_method = "Match Stats"

    # write class that automatically re-runs styling analysis on post_processed_df
    # that way if post_processed_df has different column names then the default dataframe
    # the new column names are dipslayed,  tailor made for this situation
    # ... or these should be different pinned rows
    # nope pinned rows don't work, because then we'd have to change column names still, or have
    # a bunch of empty columns
        
    datacompy_post_processing_klasses = [
        DfHeader, ColumnSummary, RowSummary, ColumnMatching, MatchStats]
    
    base_a_klasses = BuckarooWidget.analysis_klasses.copy()
    base_a_klasses.extend(datacompy_post_processing_klasses)
    class DatacompyBuckarooWidget(BuckarooWidget):
        analysis_klasses = base_a_klasses


        #the following should move to 
        def __init__(self, orig_df, debug=False,
                     column_config_overrides=None,
                     pinned_rows=None, extra_grid_config=None,
                     component_config=None, init_sd=None):
            if init_sd is None:
                self.init_sd = {}
            else:
                self.init_sd = init_sd
            super().__init__(
                orig_df, debug, column_config_overrides, pinned_rows, extra_grid_config, component_config)

        @observe('summary_sd')
        @exception_protect('merged_sd-protector')
        def _merged_sd(self, change):
            #slightly inconsitent that processed_sd gets priority over
            #summary_sd, given that processed_df is computed first. My
            #thinking was that processed_sd has greater total knowledge
            #and should supersede summary_sd.
            self.merged_sd = merge_sds(
                self.init_sd, self.cleaned_sd, self.summary_sd, self.processed_sd)

    joined_df, column_config_overrides, init_sd = col_join_dfs(df1, df2, cmp)
    index_first_sd = merge_sds({'index':{}}, init_sd)
    dcbw = DatacompyBuckarooWidget(
        joined_df, column_config_overrides=column_config_overrides, init_sd=index_first_sd,
        pinned_rows=[
        {'primary_key_val': 'unequality',     'displayer_args': {'displayer': 'obj' } }]
    )

    return dcbw

from buckaroo.customizations.styling import (DefaultMainStyling)
class MergingMainStylingAnalysis(DefaultMainStyling):

    @classmethod
    def style_columns(kls, sd):
        print("merging main styling")
        ret_col_config = []

        #this is necessary for polars to add an index column, which is
        #required so that summary_stats makes sense
        if 'index' not in sd:
            ret_col_config.append({'col_name': 'index', 'displayer_args': {'displayer': 'obj'}})
            
        for col in sd.keys():
            col_meta = sd[col]
            if col_meta.get('merge_rule') == 'hidden':
                #new addition add to base styling analysis
                #add unit test
                continue

            base_style = kls.style_column(col, col_meta)
            if 'column_config_override' in col_meta:
                #column_config_override, sent by the instantiation, gets set later
                base_style.update(col_meta['column_config_override'])
            ret_col_config.append(base_style)
            
        return {
            'pinned_rows': kls.pinned_rows,
            'column_config': ret_col_config,
            'extra_grid_config': kls.extra_grid_config,
            'component_config': kls.component_config
        }


"""
dual display
iterate over columns from df_1 first
if col in df2 also, note that
all df2 only columns will be at the end


histograms
have row for df_1 histogram
have row for df_2 histogram

histogram empty when column not matched

if columns exactly matched, both numeric histograms in green color

if column values exactly matched no reason to show the other dataframe column

if column values differ a couple of options, handled via styling
compact = highlight differences, as in error handling, show the other value via hover
both show df_2 column next to df_1, df2 empty except for difference

For now don't do any joining of the df,  assume equal indexes, don't want to deal with that right now

"""

class Df1Histogram(ColAnalysis):
    provides_defaults = dict(
        df_1_histogram= [[],[]], histogram_args=[], histogram_bins=[])

    requires_summary = ['histogram', 'compare_unequal_cnt', 'source_df']


    @staticmethod
    def computed_summary(summary_dict):
        if summary_dict['source_df'] == 'both':
            return {'df_1_histogram': summary_dict['histogram']
        return {'histogram':categorical_histogram(length, value_counts, nan_per)}

class Df2Histogram(ColAnalysis):
    provides_defaults = dict(
        df_2_histogram= [[],[]], histogram_args=[], histogram_bins=[])

    requires_summary = ['histogram', 'compare_equal']


    @staticmethod
    def computed_summary(summary_dict):
        return {'histogram':categorical_histogram(length, value_counts, nan_per)}

dcbw = DatacompyBuckaroo(df_a, df_b)
dcbw

