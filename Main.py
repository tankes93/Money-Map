import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import json
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ttkbootstrap as tb
import csv
from datetime import datetime
from PIL import Image, ImageTk

# Fix matplotlib permission issues
os.environ['MPLCONFIGDIR'] = os.path.join(os.getcwd(), 'matplotlib_config')

class BudgetHandler:
    def __init__(self, root):
        self.root = root
        self.root.title("Money Map")
        self.root.geometry("1000x750")
        self.root.resizable(False, False)

        # Initialize variables
        self.balance = 0
        self.transactions = []
        self.budgets = {}
        self.categories = ["Salary", "Food", "Rent", "Utilities", "Entertainment", "Others"]

        # Style configuration
        self.style = tb.Style("darkly")
        self.current_theme = "darkly"

        # Load data
        self.load_data()

        # Setup UI
        self.create_widgets()
        self.setup_bindings()

        # Set window icon
        self.set_window_icon()

    def create_widgets(self):
        # Main container
        main_frame = tb.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel (Inputs and controls)
        left_frame = tb.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Right panel (Transactions and budgets)
        right_frame = tb.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # Balance display
        self.balance_label = tb.Label(left_frame, text=f"Balance: €{self.balance:.2f}",
                                    font=("Arial", 16, "bold"), bootstyle="success")
        self.balance_label.pack(pady=10)

        # Date Entry
        date_frame = tb.Frame(left_frame)
        date_frame.pack(pady=5)
        tb.Label(date_frame, text="Date (DD-MM-YYYY):").pack(side=tk.LEFT)
        self.date_entry = tb.Entry(date_frame, width=15)
        self.date_entry.pack(side=tk.LEFT, padx=5)
        self.date_entry.insert(0, datetime.now().strftime("%d-%m-%Y"))

        # Transaction inputs
        input_frame = tb.LabelFrame(left_frame, text="Transaction Details", bootstyle="info")
        input_frame.pack(pady=10, fill=tk.X)

        tb.Label(input_frame, text="Description:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.description_entry = tb.Entry(input_frame)
        self.description_entry.grid(row=0, column=1, pady=2)

        tb.Label(input_frame, text="Amount:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.amount_entry = tb.Entry(input_frame)
        self.amount_entry.grid(row=1, column=1, pady=2)

        tb.Label(input_frame, text="Category:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.category_combobox = tb.Combobox(input_frame, values=self.categories)
        self.category_combobox.grid(row=2, column=1, pady=2)
        self.category_combobox.set(self.categories[0])

        # Custom category entry for transactions
        self.custom_category_entry_transaction = tb.Entry(input_frame)
        self.custom_category_entry_transaction.grid(row=3, column=1, pady=2)
        self.custom_category_entry_transaction.grid_remove()  # Hide initially

        # Transaction buttons
        btn_frame = tb.Frame(left_frame)
        btn_frame.pack(pady=10)
        self.add_income_btn = tb.Button(btn_frame, text="Add Income", command=self.add_income,
                                      bootstyle="success-outline")
        self.add_income_btn.pack(side=tk.LEFT, padx=2)
        self.add_expense_btn = tb.Button(btn_frame, text="Add Expense", command=self.add_expense,
                                       bootstyle="danger-outline")
        self.add_expense_btn.pack(side=tk.LEFT, padx=2)

        # Budget controls
        budget_frame = tb.LabelFrame(left_frame, text="Budget Management", bootstyle="info")
        budget_frame.pack(pady=10, fill=tk.X)

        tb.Label(budget_frame, text="Amount:").grid(row=0, column=0, pady=2)
        self.budget_amount = tb.Entry(budget_frame)
        self.budget_amount.grid(row=0, column=1, pady=2)

        tb.Label(budget_frame, text="Category:").grid(row=1, column=0, pady=2)
        self.budget_category = tb.Combobox(budget_frame, values=self.categories)
        self.budget_category.grid(row=1, column=1, pady=2)
        self.budget_category.set(self.categories[0])

        # Custom category entry for budgets
        self.custom_category_entry_budget = tb.Entry(budget_frame)
        self.custom_category_entry_budget.grid(row=2, column=1, pady=2)
        self.custom_category_entry_budget.grid_remove()  # Hide initially

        budget_btn_frame = tb.Frame(budget_frame)
        budget_btn_frame.grid(row=3, columnspan=2, pady=5)
        tb.Button(budget_btn_frame, text="Set Budget", command=self.set_budget,
                 bootstyle="warning-outline").pack(side=tk.LEFT, padx=2)
        tb.Button(budget_btn_frame, text="Remove Budget", command=self.remove_budget,
                 bootstyle="danger-outline").pack(side=tk.LEFT, padx=2)
        tb.Button(budget_btn_frame, text="View Budgets", command=self.view_budgets,
                 bootstyle="info-outline").pack(side=tk.LEFT, padx=2)

        # Transaction table
        transaction_frame = tb.Frame(right_frame)
        transaction_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.transaction_tree = tb.Treeview(transaction_frame, columns=("Date", "Description", "Amount", "Category", "Type"),
                                          show="headings", height=15)
        self.transaction_tree.heading("Date", text="Date")
        self.transaction_tree.heading("Description", text="Description")
        self.transaction_tree.heading("Amount", text="Amount")
        self.transaction_tree.heading("Category", text="Category")
        self.transaction_tree.heading("Type", text="Type")
        self.transaction_tree.pack(fill=tk.BOTH, expand=True)

        # Add horizontal scrollbar
        scrollbar_x = tb.Scrollbar(transaction_frame, orient=tk.HORIZONTAL, command=self.transaction_tree.xview)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.transaction_tree.configure(xscrollcommand=scrollbar_x.set)

        # Filter controls
        filter_frame = tb.Frame(right_frame)
        filter_frame.pack(pady=5, fill=tk.X)

        tb.Label(filter_frame, text="Filter by Category:").pack(side=tk.LEFT)
        self.filter_category = tb.Combobox(filter_frame, values=["All"] + self.categories)
        self.filter_category.pack(side=tk.LEFT, padx=5)
        self.filter_category.set("All")

        tb.Label(filter_frame, text="Start Date:").pack(side=tk.LEFT, padx=5)
        self.start_date = tb.Entry(filter_frame, width=10)
        self.start_date.pack(side=tk.LEFT)

        tb.Label(filter_frame, text="End Date:").pack(side=tk.LEFT, padx=5)
        self.end_date = tb.Entry(filter_frame, width=10)
        self.end_date.pack(side=tk.LEFT)

        tb.Button(filter_frame, text="Apply Filters", command=self.update_ui,
                 bootstyle="secondary-outline").pack(side=tk.LEFT, padx=5)

        # Control buttons
        control_frame = tb.Frame(right_frame)
        control_frame.pack(pady=10, fill=tk.X)

        tb.Button(control_frame, text="Transaction Report", command=self.show_transaction_report,
                 bootstyle="primary-outline").pack(side=tk.LEFT, padx=2)
        tb.Button(control_frame, text="Budget Report", command=self.show_budget_report,
                 bootstyle="primary-outline").pack(side=tk.LEFT, padx=2)
        tb.Button(control_frame, text="Export CSV", command=self.export_csv,
                 bootstyle="success-outline").pack(side=tk.LEFT, padx=2)
        tb.Button(control_frame, text="Delete Data", command=self.delete_data,
                 bootstyle="danger-outline").pack(side=tk.LEFT, padx=2)
        tb.Button(control_frame, text="Toggle Theme", command=self.toggle_theme,
                 bootstyle="secondary-outline").pack(side=tk.LEFT, padx=2)

        # Context menu for transactions
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.edit_transaction)
        self.context_menu.add_command(label="Delete", command=self.delete_transaction)

        self.update_ui()

    def setup_bindings(self):
        self.transaction_tree.bind("<Button-3>", self.show_context_menu)
        self.category_combobox.bind("<<ComboboxSelected>>", self.toggle_custom_category_transaction)
        self.budget_category.bind("<<ComboboxSelected>>", self.toggle_custom_category_budget)

    def show_context_menu(self, event):
        item = self.transaction_tree.identify_row(event.y)
        if item:
            self.transaction_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def load_data(self):
        # Load transactions
        if os.path.exists("transactions.json"):
            with open("transactions.json", "r") as f:
                data = json.load(f)
                self.transactions = data.get("transactions", [])
                self.balance = data.get("balance", 0)

        # Load budgets
        if os.path.exists("budgets.json"):
            with open("budgets.json", "r") as f:
                self.budgets = json.load(f)

    def save_data(self):
        with open("transactions.json", "w") as f:
            json.dump({"balance": self.balance, "transactions": self.transactions}, f, indent=2)

        with open("budgets.json", "w") as f:
            json.dump(self.budgets, f, indent=2)

    def delete_data(self):
        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete all data?")
        if confirm:
            self.transactions = []
            self.budgets = {}
            self.balance = 0
            self.save_data()
            self.update_ui()
            messagebox.showinfo("Success", "All data has been deleted successfully!")

    def update_ui(self):
        # Update balance
        self.balance_label.config(text=f"Balance: €{self.balance:.2f}",
                                bootstyle="success" if self.balance >= 0 else "danger")

        # Filter transactions
        filtered = self.transactions
        category_filter = self.filter_category.get()
        start_date = self.start_date.get()
        end_date = self.end_date.get()

        if category_filter != "All":
            filtered = [t for t in filtered if t["category"] == category_filter]

        try:
            if start_date:
                start = datetime.strptime(start_date, "%d-%m-%Y")
                filtered = [t for t in filtered if datetime.strptime(t["date"], "%d-%m-%Y") >= start]
            if end_date:
                end = datetime.strptime(end_date, "%d-%m-%Y")
                filtered = [t for t in filtered if datetime.strptime(t["date"], "%d-%m-%Y") <= end]
        except ValueError:
            messagebox.showerror("Invalid Date", "Please use DD-MM-YYYY format")

        # Update transaction list
        self.transaction_tree.delete(*self.transaction_tree.get_children())
        for t in filtered:
            amount = f"€{t['amount']:.2f}"
            category = t["category"]
            description = t["description"]
            date = t["date"]
            transaction_type = "Income" if t["amount"] > 0 else "Expense"
            self.transaction_tree.insert("", "end", values=(date, description, amount, category, transaction_type))

    def add_income(self):
        self.add_transaction(is_income=True)

    def add_expense(self):
        self.add_transaction(is_income=False)

    def add_transaction(self, is_income):
        description = self.description_entry.get()
        amount = self.amount_entry.get()
        date_str = self.date_entry.get()

        if not all([description, amount, date_str]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        try:
            # Validate date format
            date_obj = datetime.strptime(date_str, "%d-%m-%Y")
            formatted_date = date_obj.strftime("%d-%m-%Y")
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive.")

            category = self.category_combobox.get()
            if category == "Others":
                category = self.custom_category_entry_transaction.get()
                if not category:
                    messagebox.showerror("Error", "Please enter a custom category name.")
                    return

            if not is_income and amount > self.balance:
                messagebox.showerror("Error", "Insufficient balance!")
                return

            # Check budget
            if not is_income and not self.check_budget(category, amount):
                return

            amount = amount if is_income else -amount
            self.balance += amount
            self.transactions.append({
                "date": formatted_date,
                "description": description,
                "amount": amount,
                "category": category
            })
            self.update_ui()
            messagebox.showinfo("Success", "Transaction added successfully!")
            self.clear_entries()
            self.save_data()

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")

    def edit_transaction(self):
        selected = self.transaction_tree.selection()
        if not selected:
            return

        index = self.transaction_tree.index(selected[0])
        transaction = self.transactions[index]

        # Populate fields
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, transaction["date"])
        self.description_entry.delete(0, tk.END)
        self.description_entry.insert(0, transaction["description"])
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.insert(0, abs(transaction["amount"]))
        self.category_combobox.set(transaction["category"])

        # Temporarily change button functions
        self.add_income_btn.config(text="Save Changes", command=lambda: self.save_edit(index, is_income=transaction["amount"] > 0))
        self.add_expense_btn.config(text="Cancel", command=self.cancel_edit)

    def cancel_edit(self):
        self.clear_entries()
        self.add_income_btn.config(text="Add Income", command=self.add_income)
        self.add_expense_btn.config(text="Add Expense", command=self.add_expense)

    def save_edit(self, index, is_income):
        description = self.description_entry.get()
        amount = self.amount_entry.get()
        date_str = self.date_entry.get()

        if not all([description, amount, date_str]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        try:
            # Validate date format
            date_obj = datetime.strptime(date_str, "%d-%m-%Y")
            formatted_date = date_obj.strftime("%d-%m-%Y")
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive.")

            category = self.category_combobox.get()
            if category == "Others":
                category = self.custom_category_entry_transaction.get()
                if not category:
                    messagebox.showerror("Error", "Please enter a custom category name.")
                    return

            if not is_income and amount > self.balance + abs(self.transactions[index]["amount"]):
                messagebox.showerror("Error", "Insufficient balance!")
                return

            # Check budget
            if not is_income and not self.check_budget(category, amount):
                return

            # Update transaction
            old_amount = self.transactions[index]["amount"]
            self.balance -= old_amount  # Remove old amount
            new_amount = amount if is_income else -amount
            self.balance += new_amount  # Add new amount

            self.transactions[index] = {
                "date": formatted_date,
                "description": description,
                "amount": new_amount,
                "category": category
            }

            self.update_ui()
            messagebox.showinfo("Success", "Transaction updated successfully!")
            self.clear_entries()
            self.save_data()

            # Reset buttons
            self.add_income_btn.config(text="Add Income", command=self.add_income)
            self.add_expense_btn.config(text="Add Expense", command=self.add_expense)

        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")

    def delete_transaction(self):
        selected = self.transaction_tree.selection()
        if not selected:
            return

        index = self.transaction_tree.index(selected[0])
        amount = self.transactions[index]["amount"]
        self.balance -= amount
        del self.transactions[index]
        self.update_ui()
        self.save_data()
        messagebox.showinfo("Success", "Transaction deleted successfully!")

    def set_budget(self):
        category = self.budget_category.get()
        if category == "Others":
            category = self.custom_category_entry_budget.get()
            if not category:
                messagebox.showerror("Error", "Please enter a custom category name.")
                return

        try:
            amount = float(self.budget_amount.get())
            if amount <= 0:
                raise ValueError
            self.budgets[category] = amount
            self.save_data()
            messagebox.showinfo("Success", f"Budget set for {category}")
        except (ValueError, tk.TclError):
            messagebox.showerror("Invalid Amount", "Please enter a positive number")

    def remove_budget(self):
        category = self.budget_category.get()
        if category == "Others":
            category = self.custom_category_entry_budget.get()
            if not category:
                messagebox.showerror("Error", "Please enter a custom category name.")
                return

        if category in self.budgets:
            del self.budgets[category]
            self.save_data()
            messagebox.showinfo("Success", f"Budget removed for {category}")

    def check_budget(self, category, amount):
        if category in self.budgets:
            spent = sum(t["amount"] for t in self.transactions
                      if t["category"] == category and t["amount"] < 0)
            remaining = self.budgets[category] + spent
            if abs(amount) > remaining:
                messagebox.showerror("Budget Exceeded",
                                   f"This purchase exceeds your {category} budget by €{abs(amount) - remaining:.2f}")
                return False
        return True

    def show_transaction_report(self):
        expenses = {}
        for transaction in self.transactions:
            if transaction["amount"] < 0:
                expenses[transaction["category"]] = expenses.get(transaction["category"], 0) + abs(transaction["amount"])

        if not expenses:
            messagebox.showerror("Error", "No expenses recorded yet.")
            return

        graph_window = tk.Toplevel(self.root)
        graph_window.title("Transaction Report")
        graph_window.geometry("600x500")

        # Set window icon
        self.set_window_icon(graph_window)

        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(expenses.values(), labels=expenses.keys(), autopct="%1.1f%%", startangle=140)
        ax.set_title("Expense Breakdown")

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

        # Add a button to switch to bar graph
        switch_btn = tb.Button(graph_window, text="Switch to Bar Graph", command=lambda: self.show_bar_graph(expenses, graph_window), bootstyle="info-outline")
        switch_btn.pack(pady=10)

    def show_bar_graph(self, expenses, graph_window):
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.bar(expenses.keys(), expenses.values(), color='skyblue')
        ax.set_title("Expense Breakdown")
        ax.set_xlabel("Category")
        ax.set_ylabel("Amount (€)")

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

        # Add a button to switch to pie graph
        switch_btn = tb.Button(graph_window, text="Switch to Pie Graph", command=lambda: self.show_pie_graph(expenses, graph_window), bootstyle="info-outline")
        switch_btn.pack(pady=10)

    def show_pie_graph(self, expenses, graph_window):
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(expenses.values(), labels=expenses.keys(), autopct="%1.1f%%", startangle=140)
        ax.set_title("Expense Breakdown")

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        canvas.draw()

        # Add a button to switch to bar graph
        switch_btn = tb.Button(graph_window, text="Switch to Bar Graph", command=lambda: self.show_bar_graph(expenses, graph_window), bootstyle="info-outline")
        switch_btn.pack(pady=10)

    def show_budget_report(self):
        budget_window = tk.Toplevel(self.root)
        budget_window.title("Budget Report")
        budget_window.geometry("600x500")

        # Set window icon
        self.set_window_icon(budget_window)

        category_frame = tb.Frame(budget_window)
        category_frame.pack(pady=10)

        tb.Label(category_frame, text="Category:").pack(side=tk.LEFT)
        category_combobox = tb.Combobox(category_frame, values=[""] + self.categories)
        category_combobox.pack(side=tk.LEFT, padx=5)
        category_combobox.set("")

        def update_budget_graph(event):
            category = category_combobox.get()
            if category == "":
                return

            if category not in self.budgets:
                messagebox.showerror("Error", f"No budget set for {category}")
                return

            spent = sum(t["amount"] for t in self.transactions
                        if t["category"] == category and t["amount"] < 0)
            remaining = self.budgets[category] + spent

            if remaining < 0:
                remaining = 0

            fig, ax = plt.subplots(figsize=(5, 5))
            ax.pie([remaining, abs(spent)], labels=["Remaining", "Spent"], autopct="%1.1f%%", startangle=140)
            ax.set_title(f"Budget Utilization for {category}")

            canvas = FigureCanvasTkAgg(fig, master=budget_window)
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            canvas.draw()

        category_combobox.bind("<<ComboboxSelected>>", update_budget_graph)

        # Initial graph
        update_budget_graph(None)

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Description", "Amount", "Category"])
                for t in self.transactions:
                    writer.writerow([t["date"], t["description"], t["amount"], t["category"]])
            messagebox.showinfo("Success", "Transactions exported successfully!")

    def toggle_theme(self):
        self.current_theme = "cosmo" if self.current_theme == "darkly" else "darkly"
        self.style = tb.Style(self.current_theme)
        self.style.theme_use(self.current_theme)
        self.update_combobox_styles()

    def update_combobox_styles(self):
        self.category_combobox.configure(style=f"{self.current_theme}.TCombobox")
        self.budget_category.configure(style=f"{self.current_theme}.TCombobox")
        self.filter_category.configure(style=f"{self.current_theme}.TCombobox")

    def clear_entries(self):
        self.description_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%d-%m-%Y"))  # Reset to current date
        self.category_combobox.set(self.categories[0])
        self.custom_category_entry_transaction.delete(0, tk.END)
        self.custom_category_entry_transaction.grid_remove()  # Hide custom category entry
        self.budget_amount.delete(0, tk.END)
        self.budget_category.set(self.categories[0])
        self.custom_category_entry_budget.delete(0, tk.END)
        self.custom_category_entry_budget.grid_remove()  # Hide custom category entry

    def toggle_custom_category_transaction(self, event):
        if self.category_combobox.get() == "Others":
            self.custom_category_entry_transaction.grid()  # Show custom category entry
        else:
            self.custom_category_entry_transaction.grid_remove()  # Hide custom category entry

    def toggle_custom_category_budget(self, event):
        if self.budget_category.get() == "Others":
            self.custom_category_entry_budget.grid()  # Show custom category entry
        else:
            self.custom_category_entry_budget.grid_remove()  # Hide custom category entry

    def view_budgets(self):
        budget_window = tk.Toplevel(self.root)
        budget_window.title("View Budgets")
        budget_window.geometry("300x200")

        # Set window icon
        self.set_window_icon(budget_window)

        budget_list = tk.Listbox(budget_window, width=50)
        budget_list.pack(pady=10)

        for category, amount in self.budgets.items():
            budget_list.insert(tk.END, f"{category}: €{amount:.2f}")

    def set_window_icon(self, window=None):
        if window is None:
            window = self.root

        try:
            img = Image.open("logo.png")
            img = img.resize((32, 32))  # Adjust size as needed
            icon_image = ImageTk.PhotoImage(img)
            window.iconphoto(True, icon_image)
        except Exception as e:
            print(f"Error setting window icon: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the main window initially

    # Splash screen implementation
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.attributes("-topmost", True)

    try:
        img = Image.open("logo.png")
        img = img.resize((300, 300))  # Adjust size as needed

        # Remove background and set transparent
        splash.configure(bg='white')
        splash.attributes('-transparentcolor', 'white')

        splash_image = ImageTk.PhotoImage(img)
        label = tk.Label(splash, image=splash_image, bg='white')
        label.image = splash_image
        label.pack()

        # Center splash screen
        splash.update_idletasks()
        width = splash.winfo_width()
        height = splash.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        splash.geometry(f"+{x}+{y}")

        # Close splash after 5 seconds and show main window
        splash.after(5000, lambda: [splash.destroy(), root.deiconify()])
    except Exception as e:
        print(f"Splash screen error: {e}")
        splash.destroy()
        root.deiconify()

    app = BudgetHandler(root)
    root.mainloop()
