import re


class Form1325HebrewText:
    # Form Titles
    LEFT_HEADER = "דוח שנתי 2023\n1325\n"
    TITLE_1 = "נספח ג(1) לטופס הדוח השנתי"
    TITLE_2 = "רווח הון מניירות ערך סחירים(1) לשנת המס 2023"
    TITLE_3 = "יש למלא טופס נפרד עבור כל רווח הון בשיעור מס שונה(2)  הטופס מיועד לדווח על רווח הון ריאלי ממכירת " \
              "ניירות ערך<br/>נסחרים בבורסה בידי חבר בני אדם או בידי יחיד שניירות הערך רשומים בספרי העסק וכן יחיד " \
              "שלא נוכה לו מס כחוק.<br/>הטופס אינו מיועד לניירות ערך שחלות עליהם הוראות המעבר לביטול סעיף 6 לחוק " \
              "התיאומים."

    # Personal details table headers
    NAME = "שם הנישום"
    FILE_NUMBER = "מספר תיק"
    ASSET_ABROAD = 'נכס בחו״ל'
    YES = "כן"
    NO = "לא"

    # Table headers
    ROW_NUMBER = ""
    SYMBOL = "זיהוי מלא של נייר הערך שנמכר לפי הסדר הכרונולוגי של המכירות"
    BOUGHT_DURING_PRE_MARKET = "נרכש טרם הרישום למסחר"
    SHARES = "ערך נקוב במכירה"
    BUY_DATE = "תאריך הרכישה"
    BUY_AMOUNT = "מחיר מקורי (3)"
    RATE_CHANGE = "1 + שיעור עליית המדד (4)"
    BUY_AMOUNT_ADJUSTED = "מחיר מתואם"
    SELL_DATE = "תאריך המכירה"
    SELL_AMOUNT = "תמורה (5)"
    PROFIT = "רווח הון (2) ריאלי בשיעור מס של 25%"
    LOSS = "הפסד הון(6) (ד-א) או הפסד הון ריאלי לפי סעיף 9(ג) לחוק התיאומים(7)"

    # Table sub-headers
    COL1 = ""
    COL2 = COL1
    COL3 = "אם כן סמן √"
    COL4 = COL1
    COL5 = "שנה/חודש/יום"
    COL6 = "א"
    COL7 = "ב"
    COL8 = "(א X ב) = ג"
    COL9 = COL5
    COL10 = "ד"
    COL11 = "(ג - ד)"
    COL12 = COL1
    SUB_HEADER = [COL1, COL2, COL3, COL4, COL5, COL6, COL7, COL8, COL9, COL10, COL11, COL12]

    # Totals tables
    TOTAL_PROFIT_LOSS = 'סה״כ רווח הון/הפסד הון'
    TOTAL_PROFIT_LOSS_COMMENT = 'יועבר לנספח ג למשבצת המתאימה על-פי שיעורי המס'
    TOTAL_SALES = 'סכום מכירות'
    TOTAL_SALES_COMMENT = 'יועבר לנספח ג למשבצת המתאימה'

    COMMENT = "הערה: בעל מניות מהותי, התובע רווחים ראויים לחלוקה, ימלא טופס 1399(י) או 1399(ח)(8)"

    SIGNATURE_1 = "חתימה"
    SIGNATURE_2 = "חותמת המייצג לשם זיהוי"

    @staticmethod
    def cite(text):
        pattern = r"\((\d+)\)"

        # Define the replacement function
        def replacer(match):
            number = match.group(1)
            return f'<cite class="small-cite">({number})</cite>'

        # Use re.sub with the replacement function
        result = re.sub(pattern, replacer, text)
        return result
