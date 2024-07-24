import csv
from decimal import Decimal
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import AccountBalance, Expense, ExpenseType, Income, IncomeType, Report
from .forms import ExpenseForm, IncomeForm, ReportForm, ExpenseTypeForm
from datetime import datetime


CURRENCY_RATES = {
    'USD': 12587.08,
    'RUB': 143.28,
    'UZS': 1
}
def set_currency(request):
    currency = request.GET.get('currency', None)
    next_url = request.GET.get('next', '/')
    
    if currency:
        request.session['currency'] = currency
        messages.success(request, f'Currency changed to {currency}.')
    else:
        messages.error(request, 'Currency not specified.')

    return redirect(next_url)
def convert_to_uzs(amount, currency):
    if currency not in CURRENCY_RATES:
        raise ValueError("Unsupported currency type")
    return amount * Decimal(CURRENCY_RATES[currency])

def get_selected_currency(request):
    return request.GET.get('currency', 'USD')

@login_required
def index(request):
    selected_currency = get_selected_currency(request)
    expenses = Expense.objects.all()
    incomes = Income.objects.all()

    total_expenses = sum(convert_to_uzs(expense.amount, expense.currency) for expense in expenses)
    total_incomes = sum(convert_to_uzs(income.amount, income.currency) for income in incomes)

    converted_total_expenses = total_expenses / Decimal(CURRENCY_RATES[selected_currency])
    converted_total_incomes = total_incomes / Decimal(CURRENCY_RATES[selected_currency])

    balance = total_incomes - total_expenses
    converted_balance = balance / Decimal(CURRENCY_RATES[selected_currency])

    transactions = []
    for expense in expenses:
        transactions.append({
            'date': expense.date.strftime('%Y-%m-%d'),
            'amount': -convert_to_uzs(expense.amount, expense.currency) / Decimal(CURRENCY_RATES[selected_currency]),
            'type': 'expense'
        })
    for income in incomes:
        transactions.append({
            'date': income.date.strftime('%Y-%m-%d'),
            'amount': convert_to_uzs(income.amount, income.currency) / Decimal(CURRENCY_RATES[selected_currency]),
            'type': 'income'
        })

    context = {
        'expenses': expenses,
        'incomes': incomes,
        'total_expenses': converted_total_expenses,
        'total_incomes': converted_total_incomes,
        'balance': converted_balance,
        'currency': selected_currency,
        'transactions': transactions,
    }
    return render(request, 'history/index.html', context)


@login_required
def add_expense(request):
    selected_currency = request.session.get('currency', 'USD')
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            manual_expense_type = form.cleaned_data.get('manual_expense_type')
            expense_type = form.cleaned_data.get('expense_type')

            if manual_expense_type:
                expense.expense_type = None
                expense.manual_expense_type = manual_expense_type
            elif expense_type:
                expense.manual_expense_type = None
                expense.expense_type = expense_type
            else:
                messages.error(request, 'Please select or enter an expense type.')
                return render(request, 'history/add_expense.html', {'form': form, 'expense_types': ExpenseType.objects.all(), 'currency': selected_currency})

            account_balance, created = AccountBalance.objects.get_or_create(user=request.user, wallet_type='default')
            expense_amount_in_uzs = convert_to_uzs(expense.amount, expense.currency)
            if account_balance.balance >= expense_amount_in_uzs:
                expense.account_balance = account_balance
                account_balance.balance -= expense_amount_in_uzs
                account_balance.save()
                expense.save()
                messages.success(request, 'Expense added successfully.')
                return redirect(f'{reverse("index")}?currency={selected_currency}')
            else:
                messages.error(request, 'You do not have enough funds in your account.')
    else:
        form = ExpenseForm()

    expense_types = ExpenseType.objects.all()
    return render(request, 'history/add_expense.html', {'form': form, 'expense_types': expense_types, 'currency': selected_currency})
@login_required
def add_income(request):
    selected_currency = get_selected_currency(request)
    if request.method == 'POST':
        form = IncomeForm(request.POST, request.FILES)
        if form.is_valid():
            income = form.save(commit=False)
            manual_income_type = form.cleaned_data.get('manual_income_type')
            manual_income_image = form.cleaned_data.get('manual_income_image')

            if manual_income_type:
                income_type, created = IncomeType.objects.get_or_create(name=manual_income_type)
                if manual_income_image:
                    income_type.image = manual_income_image
                    income_type.save()
                income.income_type = income_type

            income.account_balance = AccountBalance.objects.get_or_create(user=request.user, wallet_type='default')[0]
            income_amount_in_uzs = convert_to_uzs(income.amount, income.currency)
            income.account_balance.balance += income_amount_in_uzs
            income.account_balance.save()
            income.save()
            messages.success(request, 'Income added successfully.')
            return redirect(f"{reverse('index')}?currency={selected_currency}")
        else:
            messages.error(request, 'There was an error with your form.')
    else:
        form = IncomeForm()

    income_types = IncomeType.objects.all()
    return render(request, 'history/add_income.html', {'form': form, 'income_types': income_types, 'currency': selected_currency})

@login_required
def edit_expense(request, pk):
    selected_currency = get_selected_currency(request)
    expense = get_object_or_404(Expense, pk=pk)
    old_amount_in_uzs = convert_to_uzs(expense.amount, expense.currency)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            new_expense = form.save(commit=False)
            new_amount_in_uzs = convert_to_uzs(new_expense.amount, new_expense.currency)
            account_balance = expense.account_balance
            new_balance = account_balance.balance + old_amount_in_uzs - new_amount_in_uzs
            if new_balance >= 0:
                account_balance.balance = new_balance
                account_balance.save()
                new_expense.save()
                messages.success(request, 'Expense updated successfully.')
                return redirect(f'{reverse("index")}?currency={selected_currency}')

            else:
                messages.error(request, 'You do not have enough funds in your account.')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'history/edit_expense.html', {'form': form, 'currency': selected_currency})

@login_required
def delete_expense(request, pk):
    selected_currency = get_selected_currency(request)
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        account_balance = expense.account_balance
        account_balance.balance += convert_to_uzs(expense.amount, expense.currency)
        account_balance.save()
        expense.delete()
        messages.success(request, 'Expense deleted successfully.')
        return redirect(f'{reverse("index")}?currency={selected_currency}')
    return render(request, 'history/delete_expense.html', {'expense': expense, 'currency': selected_currency})

@login_required
def edit_income(request, pk):
    selected_currency = get_selected_currency(request)
    income = get_object_or_404(Income, pk=pk)
    old_amount_in_uzs = convert_to_uzs(income.amount, income.currency)
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            new_income = form.save(commit=False)
            new_amount_in_uzs = convert_to_uzs(new_income.amount, new_income.currency)
            account_balance = income.account_balance
            account_balance.balance -= old_amount_in_uzs
            account_balance.balance += new_amount_in_uzs
            account_balance.save()
            new_income.save()
            messages.success(request, 'Income updated successfully.')
            return redirect(f'{reverse("index")}?currency={selected_currency}')

    else:
        form = IncomeForm(instance=income)
    return render(request, 'history/edit_income.html', {'form': form, 'currency': selected_currency})

@login_required
def delete_income(request, pk):
    selected_currency = get_selected_currency(request)
    income = get_object_or_404(Income, pk=pk)
    if request.method == 'POST':
        account_balance = income.account_balance
        account_balance.balance -= convert_to_uzs(income.amount, income.currency)
        account_balance.save()
        income.delete()
        messages.success(request, 'Income deleted successfully.')
        return redirect(f'{reverse("index")}?currency={selected_currency}')
    return render(request, 'history/delete_income.html', {'income': income, 'currency': selected_currency})

@login_required
def add_report(request):
    selected_currency = get_selected_currency(request)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Report added successfully.')
            return redirect(f'index?currency={selected_currency}')
    else:
        form = ReportForm()
    return render(request, 'history/add_report.html', {'form': form, 'currency': selected_currency})

@login_required
def add_expense_type(request):
    selected_currency = get_selected_currency(request)
    if request.method == 'POST':
        form = ExpenseTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense type added successfully.')
            return redirect(f'{reverse("index")}?currency={selected_currency}')

    else:
        form = ExpenseTypeForm()
    return render(request, 'history/add_expense_type.html', {'form': form, 'currency': selected_currency})

@login_required
def history(request):
    selected_currency = get_selected_currency(request)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    expenses = Expense.objects.all()
    incomes = Income.objects.all()

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        expenses = expenses.filter(date__range=(start_date, end_date))
        incomes = incomes.filter(date__range=(start_date, end_date))

    total_expenses = sum(convert_to_uzs(expense.amount, expense.currency) for expense in expenses)
    total_incomes = sum(convert_to_uzs(income.amount, income.currency) for income in incomes)
    
    converted_total_expenses = total_expenses / Decimal(CURRENCY_RATES[selected_currency])
    converted_total_incomes = total_incomes / Decimal(CURRENCY_RATES[selected_currency])
    
    balance = total_incomes - total_expenses
    converted_balance = balance / Decimal(CURRENCY_RATES[selected_currency])
    
    context = {
        'expenses': expenses,
        'incomes': incomes,
        'total_expenses': converted_total_expenses,
        'total_incomes': converted_total_incomes,
        'balance': converted_balance,
        'currency': selected_currency,
    }
    return render(request, 'history/history.html', context)


def import_transactions(request):
    selected_currency = get_selected_currency(request)
    if request.method == 'POST':
        csv_file = request.FILES['file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'This is not a CSV file')
            return redirect('import_transactions')

        file_data = csv_file.read().decode('utf-8')
        lines = file_data.split('\n')

        for line in lines:
            if not line.strip():
                continue

            fields = line.split(',')

            if len(fields) < 6: 
                messages.error(request, 'CSV file format is incorrect')
                return redirect('import_transactions')

            try:
                date = fields[0]
                amount = fields[1]
                expense_type_name = fields[2]
                manual_expense_type = fields[3]
                image = fields[4]
                account_balance_id = fields[5]

                account_balance = AccountBalance.objects.get(id=account_balance_id)  

                expense_type = None
                if expense_type_name:
                    expense_type, created = ExpenseType.objects.get_or_create(name=expense_type_name)

                Expense.objects.create(
                    date=date,
                    amount=amount,
                    expense_type=expense_type,
                    manual_expense_type=manual_expense_type or None,
                    image=image or None,
                    account_balance=account_balance
                )

            except Exception as e:
                messages.error(request, f'Error processing line: {line}. Error: {str(e)}')
                continue

        messages.success(request, 'Transactions imported successfully!')
        return redirect(f'history?currency={selected_currency}')

    return render(request, 'history/import.html', {'currency': selected_currency})
