import gspread
from google.oauth2.service_account import Credentials
from .settings import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds  = Credentials.from_service_account_file(settings.GOOGLE_CREDS_FILE,
                                              scopes=SCOPES)
ss     = gspread.authorize(creds).open_by_key(settings.SHEET_ID)

def _get_ws(name: str):
    try:
        return ss.worksheet(name)
    except gspread.WorksheetNotFound:
        return ss.add_worksheet(title=name, rows=1000, cols=30)

sales_ws  = _get_ws("Sales")
report_ws = _get_ws("Report")

# headers for Sales
if sales_ws.row_count < 1 or not sales_ws.cell(1,1).value:
    sales_ws.append_row([
        "Date‑time", "Order ID", "Customer", "Items",
        "Total", "Fee", "Net", "Status"
    ], value_input_option="USER_ENTERED")

# Report sheet — daily aggregation via QUERY formula
if report_ws.row_count < 1 or not report_ws.cell(1, 1).value:
    report_ws.update("A1:E1", [["Date", "Gross", "Fee", "Net", "Orders"]])
    formula = (
        '=ARRAYFORMULA(QUERY(Sales!A2:H, '
        '"select toDate(A), sum(E), sum(F), sum(G), count(A) '
        'where A is not null group by toDate(A) '
        'order by toDate(A) desc", 1))'
    )
    report_ws.update("A2", [[formula]], value_input_option="USER_ENTERED")