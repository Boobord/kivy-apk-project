from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.text import LabelBase
from kivy.uix.popup import Popup
import arabic_reshaper
from bidi.algorithm import get_display
import numbers
import os
import jdatetime
from xhtml2pdf import pisa  # ← عوض شد: reportlab → xhtml2pdf
import tempfile

# ثبت فونت فارسی
font_path = os.path.join(os.path.dirname(__file__), "fonts", "Vazirmatn-Medium.ttf")
LabelBase.register(name="Vazirmatn", fn_regular=font_path)

# مسیر لوگو
LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")

# اصلاح متن فارسی و راست‌چین
def fix_farsi(text):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

# تبدیل اعداد به فارسی
def to_farsi_digits(s):
    farsi_digits = {'0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
                    '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'}
    return ''.join(farsi_digits.get(ch, ch) for ch in str(s))

# فرمت عدد با کاما
def format_number(x):
    if isinstance(x, numbers.Number):
        return f"{int(x):,}"
    return str(x)


class InvoiceAppUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 10
        self.spacing = 10

        self.orders = []

        # فرم ورود آیتم
        self.inputs_layout = GridLayout(cols=2, size_hint_y=None, height=180, row_default_height=40)
        self.add_widget(self.inputs_layout)

        # شماره فاکتور
        self.inputs_layout.add_widget(Label(text=fix_farsi("شماره فاکتور:"), font_name="Vazirmatn"))
        self.invoice_number = TextInput(multiline=False, font_name="Vazirmatn")
        self.inputs_layout.add_widget(self.invoice_number)

        # نام آیتم
        self.inputs_layout.add_widget(Label(text=fix_farsi("نام آیتم:"), font_name="Vazirmatn"))
        self.item_name = TextInput(multiline=False, font_name="Vazirmatn")
        self.item_name.bind(on_text_validate=self.focus_price)
        self.inputs_layout.add_widget(self.item_name)

        # قیمت واحد
        self.inputs_layout.add_widget(Label(text=fix_farsi("قیمت واحد:"), font_name="Vazirmatn"))
        self.item_price = TextInput(multiline=False, font_name="Vazirmatn", input_filter="float")
        self.item_price.bind(on_text_validate=self.focus_count)
        self.inputs_layout.add_widget(self.item_price)

        # تعداد
        self.inputs_layout.add_widget(Label(text=fix_farsi("تعداد:"), font_name="Vazirmatn"))
        self.item_count = TextInput(multiline=False, font_name="Vazirmatn", input_filter="int")
        self.item_count.bind(on_text_validate=self.add_item)
        self.inputs_layout.add_widget(self.item_count)

        # دکمه اضافه کردن
        self.add_btn = Button(text=fix_farsi("اضافه کردن آیتم"), font_name="Vazirmatn", size_hint_y=None, height=40)
        self.add_btn.bind(on_release=self.add_item)
        self.add_widget(self.add_btn)

        # جدول آیتم‌ها
        self.scroll = ScrollView(size_hint=(1, 1))
        self.table_layout = GridLayout(cols=4, size_hint_y=None, row_default_height=30)
        self.table_layout.bind(minimum_height=self.table_layout.setter('height'))
        self.scroll.add_widget(self.table_layout)
        self.add_widget(self.scroll)

        # جمع کل
        self.subtotal_label = Label(text=fix_farsi("جمع کل: ۰ تومان"), font_name="Vazirmatn", size_hint_y=None, height=30)
        self.add_widget(self.subtotal_label)

        # دکمه چاپ فاکتور
        self.print_btn = Button(text=fix_farsi("چاپ فاکتور"), font_name="Vazirmatn", size_hint_y=None, height=40)
        self.print_btn.bind(on_release=self.print_invoice)
        self.add_widget(self.print_btn)

    def focus_price(self, *args):
        self.item_price.focus = True

    def focus_count(self, *args):
        self.item_count.focus = True

    def add_item(self, *args):
        try:
            name = self.item_name.text.strip()
            price = float(self.item_price.text or 0)
            count = int(self.item_count.text or 0)
            if not name:
                Popup(title=fix_farsi("هشدار"),
                      content=Label(text=fix_farsi("نام آیتم نمی‌تواند خالی باشد!")),
                      size_hint=(.5, .3)).open()
                return
            total = price * count
            self.orders.append({"name": name, "price": price, "count": count, "total": total})

            # بازسازی جدول
            self.table_layout.clear_widgets()
            headers = ["نام آیتم", "قیمت واحد", "تعداد", "قیمت کل"]
            for h in headers:
                self.table_layout.add_widget(Label(text=fix_farsi(h), font_name="Vazirmatn"))

            for item in self.orders:
                self.table_layout.add_widget(Label(text=fix_farsi(item["name"]), font_name="Vazirmatn"))
                self.table_layout.add_widget(Label(text=to_farsi_digits(format_number(item["price"])), font_name="Vazirmatn"))
                self.table_layout.add_widget(Label(text=to_farsi_digits(format_number(item["count"])), font_name="Vazirmatn"))
                self.table_layout.add_widget(Label(text=to_farsi_digits(format_number(item["total"])), font_name="Vazirmatn"))

            self.update_subtotal()
            self.item_name.text = ""
            self.item_price.text = ""
            self.item_count.text = ""
            self.item_name.focus = True

        except ValueError:
            Popup(title=fix_farsi("هشدار"),
                  content=Label(text=fix_farsi("لطفاً قیمت و تعداد را به‌صورت عدد وارد کنید!")),
                  size_hint=(.5, .3)).open()

    def update_subtotal(self):
        subtotal = sum(item["total"] for item in self.orders)
        self.subtotal_label.text = fix_farsi(f"جمع کل: {to_farsi_digits(format_number(subtotal))} تومان")
        return subtotal  # برگردوندن مقدار

    def print_invoice(self, *args):
        invoice_number = self.invoice_number.text.strip() or "۱"
        subtotal = self.update_subtotal()  # ← درست شد: subtotal محاسبه میشه
        self._generate_pdf(invoice_number, subtotal)

    def _generate_pdf(self, invoice_number, payable_amount):
        try:
            # مسیر فایل PDF در پوشه Download اندروید
            download_dir = "/sdcard/Download"  # ← اندروید: مسیر قابل دسترسی
            if not os.path.exists(download_dir):
                os.makedirs(download_dir, exist_ok=True)
            pdf_path = os.path.join(download_dir, f"invoice_{invoice_number}.pdf")

            # HTML برای xhtml2pdf
            now = jdatetime.datetime.now()
            items_html = ""
            for item in self.orders:
                items_html += f"""
                <tr>
                    <td style="text-align:center;">{to_farsi_digits(format_number(item["total"]))}</td>
                    <td style="text-align:center;">{to_farsi_digits(format_number(item["count"]))}</td>
                    <td style="text-align:center;">{to_farsi_digits(format_number(item["price"]))}</td>
                    <td style="text-align:right; padding-right:5px;">{fix_farsi(item["name"])}</td>
                </tr>
                """

            html = f"""
            <!DOCTYPE html>
            <html dir="rtl">
            <head>
                <meta charset="utf-8">
                <style>
                    @font-face {{ font-family: 'Vazirmatn'; src: url('file:///android_asset/Vazirmatn-Medium.ttf'); }}
                    body {{ font-family: 'Vazirmatn', sans-serif; margin: 10px; font-size: 10pt; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                    th, td {{ border: 1px solid #000; padding: 4px; }}
                    th {{ background-color: #f0f0f0; }}
                    .header {{ text-align: center; margin-bottom: 10px; }}
                    .logo {{ width: 80px; height: 80px; margin: 0 auto; display: block; }}
                    .footer {{ text-align: center; margin-top: 20px; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <img src="{LOGO_PATH}" class="logo" alt="لوگو">
                    <h2>صورتحساب</h2>
                    <p>شماره فاکتور: {to_farsi_digits(invoice_number)}</p>
                    <p>تاریخ: {to_farsi_digits(now.strftime('%Y/%m/%d'))} | ساعت: {to_farsi_digits(now.strftime('%H:%M'))}</p>
                </div>

                <table>
                    <tr>
                        <th>قیمت کل</th>
                        <th>تعداد</th>
                        <th>قیمت واحد</th>
                        <th>نام آیتم</th>
                    </tr>
                    {items_html}
                </table>

                <div style="text-align: left; margin-top: 10px;">
                    <strong>مبلغ قابل پرداخت: {to_farsi_digits(format_number(payable_amount))} تومان</strong>
                </div>

                <div class="footer">
                    یوکا — هوشمندسازی کسب‌وکار شما
                </div>
            </body>
            </html>
            """

            # ساخت PDF
            with open(pdf_path, "w+b") as f:
                pisa_status = pisa.CreatePDF(html, dest=f)

            if not pisa_status.err:
                Popup(title=fix_farsi("موفقیت"),
                      content=Label(text=fix_farsi(f"فاکتور ذخیره شد:\n{pdf_path}")),
                      size_hint=(.7, .4)).open()
            else:
                Popup(title=fix_farsi("خطا"),
                      content=Label(text=fix_farsi("خطا در ساخت PDF!")),
                      size_hint=(.5, .3)).open()

        except Exception as e:
            Popup(title=fix_farsi("خطا"),
                  content=Label(text=fix_farsi(f"خطا: {str(e)}")),
                  size_hint=(.5, .3)).open()


class InvoiceApp(App):
    def build(self):
        return InvoiceAppUI()


if __name__ == "__main__":
    InvoiceApp().run()
