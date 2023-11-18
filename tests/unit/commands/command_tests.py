import pandas as pd
import numpy as np

from buckaroo.jlisp.lispy import s
from buckaroo.jlisp.configure_utils import configure_buckaroo
from buckaroo.customizations.all_transforms import DropCol


def result_from_exec(code_str, df_input):
    RETRIEVE_RESULT_STR = '\n__ret_closure[0] = clean(__test_df)'
    outer_scope_result = [0]
    full_code_str = code_str + RETRIEVE_RESULT_STR
    exec(full_code_str, {'__test_df':df_input, '__ret_closure':outer_scope_result})
    return outer_scope_result[0]


def assert_to_py_same_transform_df(command_kls, operations, test_df):

    _a, _b, transform_df, transform_to_py = configure_buckaroo([command_kls])

    #operations = [[s('dropcol'), s('df'), "a"]]
    tdf_ops = [{'symbol': 'begin'}]
    tdf_ops.extend(operations)
    tdf = transform_df(tdf_ops, test_df.copy())
    py_code_string = transform_to_py(operations)
    edf = result_from_exec(py_code_string, test_df.copy())
    pd.testing.assert_frame_equal(tdf, edf)
    

def test_dropcol():
    base_df = pd.DataFrame({
        'a':np.random.randint(1, 10, 5), 'b':np.random.randint(1, 10, 5),
        'c':np.random.randint(1, 10, 5)})

    _a, _b, transform_df, transform_to_py = configure_buckaroo([DropCol])

    operations = [[s('dropcol'), s('df'), "a"]]
    tdf_ops = [{'symbol': 'begin'}]
    tdf_ops.extend(operations)
    tdf = transform_df(tdf_ops, base_df.copy())
    py_code_string = transform_to_py(operations)
    edf = result_from_exec(py_code_string, base_df.copy())
    pd.testing.assert_frame_equal(tdf, edf)

def test_dropcol2():
    base_df = pd.DataFrame({
        'a':np.random.randint(1, 10, 5), 'b':np.random.randint(1, 10, 5),
        'c':np.random.randint(1, 10, 5)})

    assert_to_py_same_transform_df(
        DropCol,
        [[s('dropcol'), s('df'), "a"]], base_df)
