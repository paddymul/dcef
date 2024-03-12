import polars as pl
from traitlets import Unicode
from buckaroo.buckaroo_widget import BuckarooWidget, RawDFViewerWidget
from .customizations.polars_analysis import PL_Analysis_Klasses
from .pluggable_analysis_framework.polars_analysis_management import (
    PlDfStats)
from .serialization_utils import pd_to_obj

from .customizations.styling import DefaultSummaryStatsStyling, DefaultMainStyling
from .dataflow.dataflow import Sampling
from .dataflow.autocleaning import Autocleaning
from .dataflow.widget_extension_utils import configure_buckaroo
from buckaroo.pluggable_analysis_framework.pluggable_analysis_framework import (ColAnalysis)
from buckaroo.customizations.polars_analysis import (
    VCAnalysis, PLCleaningStats, BasicAnalysis)
from buckaroo.customizations.polars_commands import (
    PlSafeInt, DropCol, FillNA, GroupBy, NoOp
)
from buckaroo.dataflow.autocleaning import AutocleaningConfig

class PLSampling(Sampling):
    pre_limit = False

local_analysis_klasses = PL_Analysis_Klasses.copy()
local_analysis_klasses.extend(
    [DefaultSummaryStatsStyling, DefaultMainStyling])


class PolarsAutocleaning(Autocleaning):
    DFStatsKlass = PlDfStats

class CleaningGenOps(ColAnalysis):
    requires_summary = ['int_parse_fail', 'int_parse']
    provides_defaults = {'cleaning_ops': []}

    int_parse_threshhold = .3
    @classmethod
    def computed_summary(kls, column_metadata):
        if column_metadata['int_parse'] > kls.int_parse_threshhold:
            return {'cleaning_ops': [{'symbol': 'safe_int', 'meta':{'auto_clean': True}}, {'symbol': 'df'}]}
        else:
            return {'cleaning_ops': []}

PL_COMMANDS = [PlSafeInt, DropCol, FillNA, GroupBy, NoOp]
class ACConf(AutocleaningConfig):
    autocleaning_analysis_klasses = [VCAnalysis, PLCleaningStats, BasicAnalysis, CleaningGenOps]
    command_klasses = PL_COMMANDS
    name="default"

class NoCleaningConfig:
    command_klasses = PL_COMMANDS
    autocleaning_analysis_klasses = []
    name = 'raw'
    
class PolarsBuckarooWidget(BuckarooWidget):
    """TODO: Add docstring here
    """
    command_classes = [DropCol, FillNA, GroupBy]
    analysis_klasses = local_analysis_klasses
    DFStatsClass = PlDfStats
    sampling_klass = PLSampling
    cleaning_method = Unicode('raw')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ac_obj = PolarsAutocleaning([
        NoCleaningConfig, ACConf])

    def _sd_to_jsondf(self, sd):
        """exists so this can be overriden for polars  """
        import pandas as pd
        temp_sd = sd.copy()

        #FIXME add actual test around weird index behavior
        # if 'index' in temp_sd:
        #     del temp_sd['index']
        return pd_to_obj(pd.DataFrame(temp_sd))

    def _build_error_dataframe(self, e):
        return pl.DataFrame({'err': [str(e)]})

    def _df_to_obj(self, df):
        # I want to this, but then row numbers are lost
        #return pd_to_obj(self.sampling_klass.serialize_sample(df).to_pandas())
        return pd_to_obj(self.sampling_klass.serialize_sample(df.to_pandas()))

def PolarsDFViewer(df,
                   column_config_overrides=None,
                   extra_pinned_rows=None, pinned_rows=None,
                   extra_analysis_klasses=None, analysis_klasses=None,
                   ):
    """
    Display a Polars DataFrame with buckaroo styling and analysis, no extra UI pieces

    column_config_overrides allows targetted specific overriding of styling

    extra_pinned_rows adds pinned_rows of summary stats
    pinned_rows replaces the default pinned rows

    extra_analysis_klasses adds an analysis_klass
    analysis_klasses replaces default analysis_klass
    """
    BuckarooKls = configure_buckaroo(
        PolarsBuckarooWidget,
        extra_pinned_rows=extra_pinned_rows, pinned_rows=pinned_rows,
        extra_analysis_klasses=extra_analysis_klasses, analysis_klasses=analysis_klasses)

    bw = BuckarooKls(df, column_config_overrides=column_config_overrides)
    dfv_config = bw.df_display_args['dfviewer_special']['df_viewer_config']
    df_data = bw.df_data_dict['main']
    summary_stats_data = bw.df_data_dict['all_stats']
    return RawDFViewerWidget(
        df_data=df_data, df_viewer_config=dfv_config, summary_stats_data=summary_stats_data)



