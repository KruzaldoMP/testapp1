from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition

from database import (
    init_db, add_log_db, update_log_db, delete_log_db,
    get_filtered_logs_db, get_summary_reports_db
)

CATEGORIES = ["Boundary", "Gas", "Parts", "Annual", "Arkila", "Special Trips"]


class TransactionRow(RecycleDataViewBehavior, BoxLayout):
    id_value = StringProperty("")
    date_value = StringProperty("")
    driver_value = StringProperty("")
    type_value = StringProperty("")
    category_value = StringProperty("")
    amount_value = StringProperty("")
    desc_value = StringProperty("")
    amount_color = ListProperty([0, 0, 0, 1])

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super().refresh_view_attrs(rv, index, data)

    def edit_pressed(self):
        App.get_running_app().open_edit_form(self.id_value)

    def delete_pressed(self):
        App.get_running_app().confirm_delete(self.id_value)


class TransactionsRV(RecycleView):
    pass


class MainScreen(Screen):
    pass


class FormScreen(Screen):
    pass


class FilterPopupContent(BoxLayout):
    pass


class TVSApp(App):
    editing_id = None

    def build(self):
        self.title = "TVS Unit Tracker"
        Window.softinput_mode = "below_target"
        init_db()

        sm = ScreenManager(transition=SlideTransition())
        self.main_screen = MainScreen(name="main")
        self.form_screen = FormScreen(name="form")
        sm.add_widget(self.main_screen)
        sm.add_widget(self.form_screen)
        self.sm = sm
        return sm

    def on_start(self):
        self.refresh_all()

    # ---------- Data refresh ----------
    def get_filter_values(self):
        ms = self.main_screen
        driver = ms.ids.filter_driver.text.strip()
        category = ms.ids.filter_category.text
        start = ms.ids.filter_start.text.strip() or None
        end = ms.ids.filter_end.text.strip() or None
        return driver, category, start, end

    def refresh_all(self):
        self.load_transactions()
        self.update_summary()

    def load_transactions(self):
        driver, category, start, end = self.get_filter_values()
        rows = get_filtered_logs_db(driver_name=driver, category=category,
                                     start_date=start, end_date=end)
        data = []
        for r in rows:
            is_income = r["type"] == "Income"
            data.append({
                "id_value": str(r["id"]),
                "date_value": r["date"],
                "driver_value": r["driver_name"],
                "type_value": r["type"],
                "category_value": r["category"],
                "amount_value": f"₱{r['amount']:,.2f}",
                "desc_value": r["description"] or "",
                "amount_color": [0.13, 0.6, 0.25, 1] if is_income else [0.75, 0.15, 0.15, 1],
            })
        self.main_screen.ids.rv.data = data
        self.main_screen.ids.empty_label.opacity = 0 if data else 1

    def update_summary(self):
        driver, _, start, end = self.get_filter_values()
        income, expense = get_summary_reports_db(driver_name=driver, start_date=start, end_date=end)
        balance = income - expense
        ms = self.main_screen
        ms.ids.lbl_income.text = f"₱{income:,.2f}"
        ms.ids.lbl_expense.text = f"₱{expense:,.2f}"
        ms.ids.lbl_balance.text = f"₱{balance:,.2f}"
        ms.ids.lbl_balance.color = (0.13, 0.6, 0.25, 1) if balance >= 0 else (0.75, 0.15, 0.15, 1)

    # ---------- Filter popup ----------
    def open_filter_popup(self):
        content = FilterPopupContent()
        ms = self.main_screen
        content.ids.pf_driver.text = ms.ids.filter_driver.text
        content.ids.pf_category.text = ms.ids.filter_category.text
        content.ids.pf_start.text = ms.ids.filter_start.text
        content.ids.pf_end.text = ms.ids.filter_end.text

        popup = Popup(title="Filter Records", content=content, size_hint=(0.9, 0.65))

        def apply_filter(*_a):
            ms.ids.filter_driver.text = content.ids.pf_driver.text
            ms.ids.filter_category.text = content.ids.pf_category.text
            ms.ids.filter_start.text = content.ids.pf_start.text
            ms.ids.filter_end.text = content.ids.pf_end.text
            popup.dismiss()
            self.refresh_all()

        def reset_filter(*_a):
            ms.ids.filter_driver.text = ""
            ms.ids.filter_category.text = "All"
            ms.ids.filter_start.text = ""
            ms.ids.filter_end.text = ""
            popup.dismiss()
            self.refresh_all()

        content.ids.btn_apply.bind(on_release=apply_filter)
        content.ids.btn_reset.bind(on_release=reset_filter)
        content.ids.btn_close.bind(on_release=popup.dismiss)
        popup.open()

    # ---------- Add / Edit form ----------
    def open_add_form(self):
        self.editing_id = None
        fs = self.form_screen
        fs.ids.form_title.text = "Add New Entry"
        fs.ids.f_date.text = datetime.now().strftime("%Y-%m-%d")
        fs.ids.f_driver.text = ""
        fs.ids.f_type.text = "Income"
        fs.ids.f_category.text = CATEGORIES[0]
        fs.ids.f_amount.text = ""
        fs.ids.f_desc.text = ""
        fs.ids.btn_delete.opacity = 0
        fs.ids.btn_delete.disabled = True
        self.sm.current = "form"

    def open_edit_form(self, log_id):
        rows = get_filtered_logs_db()
        record = next((r for r in rows if str(r["id"]) == str(log_id)), None)
        if not record:
            return
        self.editing_id = log_id
        fs = self.form_screen
        fs.ids.form_title.text = f"Edit Entry #{log_id}"
        fs.ids.f_date.text = record["date"]
        fs.ids.f_driver.text = record["driver_name"]
        fs.ids.f_type.text = record["type"]
        fs.ids.f_category.text = record["category"]
        fs.ids.f_amount.text = str(record["amount"])
        fs.ids.f_desc.text = record["description"] or ""
        fs.ids.btn_delete.opacity = 1
        fs.ids.btn_delete.disabled = False
        self.sm.current = "form"

    def save_form(self):
        fs = self.form_screen
        date = fs.ids.f_date.text.strip()
        driver = fs.ids.f_driver.text.strip()
        trans_type = fs.ids.f_type.text
        category = fs.ids.f_category.text
        amount_text = fs.ids.f_amount.text.strip()
        desc = fs.ids.f_desc.text.strip()

        if not date or not driver or not category:
            self.show_message("Missing Info", "Please fill in date, driver name and category.")
            return

        try:
            amount = float(amount_text)
        except ValueError:
            self.show_message("Invalid Amount", "Please enter a valid numeric amount.")
            return

        if self.editing_id:
            update_log_db(self.editing_id, date, driver, trans_type, category, amount, desc)
        else:
            add_log_db(date, driver, trans_type, category, amount, desc)

        self.sm.current = "main"
        self.refresh_all()

    def cancel_form(self):
        self.sm.current = "main"

    def confirm_delete(self, log_id):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text="Delete this TVS log entry?"))
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        yes_btn = Button(text="Delete")
        no_btn = Button(text="Cancel")
        btn_row.add_widget(yes_btn)
        btn_row.add_widget(no_btn)
        content.add_widget(btn_row)
        popup = Popup(title="Confirm Delete", content=content, size_hint=(0.8, 0.35))

        def do_delete(*_a):
            delete_log_db(log_id)
            popup.dismiss()
            self.refresh_all()

        yes_btn.bind(on_release=do_delete)
        no_btn.bind(on_release=popup.dismiss)
        popup.open()

    def delete_from_form(self):
        if self.editing_id:
            log_id = self.editing_id
            self.sm.current = "main"
            self.confirm_delete(log_id)

    def show_message(self, title, message):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text=message))
        btn = Button(text="OK", size_hint_y=None, height=dp(44))
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.35))
        btn.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    TVSApp().run()
