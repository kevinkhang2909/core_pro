from .GSheet import Sheet
from datetime import timedelta, datetime
from pathlib import Path
import polars as pl
import psutil
from openpyxl.utils.cell import get_column_letter, column_index_from_string, coordinate_from_string


def update_df(df, sheet_name: str, sheet_id: str, start: str = 'A1'):
    # Call sheet
    sheet = Sheet(sheet_id)
    # Dataframe type
    if isinstance(df, pl.DataFrame):
        col_df = [*df.schema.keys()]
        values = [col_df]
        values.extend(df.to_pandas().astype(str).to_numpy().tolist())
    else:
        col_df = df.columns
        values = df.transpose().reset_index().transpose().to_numpy().astype(str).tolist()
    # Export to sheets
    end = get_column_letter(len(col_df) + column_index_from_string(coordinate_from_string(start)[0]) - 1)
    sheet.clear_gsheet(sheet_name, sheet_range=f"{start}:{end}")
    sheet.update_value_single_axis(sheet_range=f"{start}:{end}", values=values,
                                   sheet_name=sheet_name, value_input='USER_ENTERED')


def format_df(sheet_name: str, sheet_id: str, num_col: int, start: str = 'A1'):
    # Sheet
    sheet = Sheet(sheet_id)
    ws_id = sheet.get_worksheet_properties(sheet_name)['sheetId']
    # Frozen
    sheet.frozen_view(ws_id)
    # Title
    sheet.format_title(ws_id, start)
    # Header
    next_start = ''.join((coordinate_from_string(start)[0], str(coordinate_from_string(start)[1] + 1)))
    sheet.format_header(ws_id, next_start, num_col)


def make_dir(folder_name):
    if not folder_name.exists():
        folder_name.mkdir(parents=True, exist_ok=True)


def update_stt(stt: str, pos: int, sheet_id: str, sheet_name: str):
    Sheet(sheet_id).update_value_single_axis(sheet_range=f'I{pos}', sheet_name=sheet_name, values=stt)


def remove_old_file(path, days: int, file_type: str):
    check_date = datetime.today().date() - timedelta(days=days)
    print(f'Files {file_type} before {check_date} ({days} days) will be removed')

    for file in Path(path).glob(f'*.{file_type}'):
        mdate = datetime.fromtimestamp(file.stat().st_mtime).date()
        if mdate < check_date:
            print(f'Remove: file {file.name} - mdate: {mdate}')
            file.unlink()


def memory_used(old: int = 0):
    mem = psutil.Process().memory_full_info().uss / (1024 ** 2)
    print(f"After {old:,.0f}MB memory is used: {mem - old:,.0f} MB, current: {mem:,.0f} MB")
    return mem
