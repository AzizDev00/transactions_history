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
from django.db import transaction

CURRENCY_RATES = {
    'USD': 12587.08,
    'RUB': 143.28,
    'UZS': 1
}

def convert_to_uzs(amount, currency):
    if currency not in CURRENCY_RATES:
        raise ValueError("Unsupported currency type")
    return amount * Decimal(CURRENCY_RATES[currency])

def get_selected_currency(request):
    return request.session.get('currency', 'USD')


import logging
logger = logging.getLogger(__name__)
@login_required
def index(request):
    selected_currency = get_selected_currency(request)
    account_balance = get_object_or_404(AccountBalance, user=request.user)

    expenses = Expense.objects.select_related('expense_type', 'account_balance').filter(account_balance__user=request.user)
    incomes = Income.objects.select_related('income_type', 'account_balance').filter(account_balance__user=request.user)

    total_expenses = sum(convert_to_uzs(expense.amount, expense.currency) for expense in expenses)
    total_incomes = sum(convert_to_uzs(income.amount, income.currency) for income in incomes)

    converted_total_expenses = total_expenses / Decimal(CURRENCY_RATES[selected_currency])
    converted_total_incomes = total_incomes / Decimal(CURRENCY_RATES[selected_currency])

    logger.debug(f"Total Expenses in UZS: {total_expenses}, Converted: {converted_total_expenses}")
    logger.debug(f"Total Incomes in UZS: {total_incomes}, Converted: {converted_total_incomes}")
    
    balance = account_balance.balance
    converted_balance = balance / Decimal(CURRENCY_RATES[selected_currency])

    transactions = [
        {
            'date': obj.date.strftime('%Y-%m-%d'),
            'amount': -convert_to_uzs(obj.amount, obj.currency) / Decimal(CURRENCY_RATES[selected_currency]),
            'type': 'expense'
        } for obj in expenses
    ] + [
        {
            'date': obj.date.strftime('%Y-%m-%d'),
            'amount': convert_to_uzs(obj.amount, obj.currency) / Decimal(CURRENCY_RATES[selected_currency]),
            'type': 'income'
        } for obj in incomes
    ]

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
    selected_currency = get_selected_currency(request)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                expense = form.save(commit=False)
                expense.user = request.user  # Ensure the expense is linked to the current user
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

                account_balance, created = AccountBalance.objects.get_or_create(user=request.user)
                expense_amount_in_uzs = convert_to_uzs(expense.amount, expense.currency)
                if account_balance.balance >= expense_amount_in_uzs:
                    account_balance.balance -= expense_amount_in_uzs
                    account_balance.save()
                    expense.account_balance = account_balance
                    expense.save()
                    messages.success(request, 'Expense added successfully.')
                else:
                    messages.error(request, 'You do not have enough funds in your account.')
                return redirect(f'{reverse("index")}?currency={selected_currency}')
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
            with transaction.atomic():
                income = form.save(commit=False)
                income.user = request.user  # Ensure the income is linked to the current user
                manual_income_type = form.cleaned_data.get('manual_income_type')
                manual_income_image = form.cleaned_data.get('manual_income_image')

                if manual_income_type:
                    income_type, created = IncomeType.objects.get_or_create(name=manual_income_type)
                    if manual_income_image:
                        income_type.image = manual_income_image
                        income_type.save()
                    income.income_type = income_type

                account_balance, created = AccountBalance.objects.get_or_create(user=request.user)
                income_amount_in_uzs = convert_to_uzs(income.amount, income.currency)
                account_balance.balance += income_amount_in_uzs
                account_balance.save()
                income.account_balance = account_balance
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
def edit_expense(request, expense_id):
    selected_currency = get_selected_currency(request)
    expense = get_object_or_404(Expense, id=expense_id, account_balance__user=request.user)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            with transaction.atomic():
                updated_expense = form.save(commit=False)
                original_amount_in_uzs = convert_to_uzs(expense.amount, expense.currency)
                updated_amount_in_uzs = convert_to_uzs(updated_expense.amount, updated_expense.currency)
                
                account_balance = expense.account_balance
                balance_change = updated_amount_in_uzs - original_amount_in_uzs
                
                if balance_change > 0 and account_balance.balance >= balance_change:
                    account_balance.balance -= balance_change
                elif balance_change < 0:
                    account_balance.balance -= balance_change 
                
                account_balance.save()
                updated_expense.save()
                messages.success(request, 'Expense updated successfully.')
                return redirect(f"{reverse('index')}?currency={selected_currency}")
    else:
        form = ExpenseForm(instance=expense)
    
    expense_types = ExpenseType.objects.all()
    return render(request, 'history/edit_expense.html', {'form': form, 'expense_types': expense_types, 'expense': expense, 'currency': selected_currency})

@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, account_balance__user=request.user)
    selected_currency = get_selected_currency(request)
    with transaction.atomic():
        account_balance = expense.account_balance
        expense_amount_in_uzs = convert_to_uzs(expense.amount, expense.currency)
        account_balance.balance -= expense_amount_in_uzs
        account_balance.save()
        expense.delete()
        messages.success(request, 'Expense deleted successfully.')
    
    return redirect(f"{reverse('index')}?currency={selected_currency}")
@login_required
def edit_income(request, income_id):
    selected_currency = get_selected_currency(request)
    income = get_object_or_404(Income, id=income_id, account_balance__user=request.user)
    
    if request.method == 'POST':
        form = IncomeForm(request.POST, request.FILES, instance=income)
        if form.is_valid():
            with transaction.atomic():
                updated_income = form.save(commit=False)
                original_amount_in_uzs = convert_to_uzs(income.amount, income.currency)
                updated_amount_in_uzs = convert_to_uzs(updated_income.amount, updated_income.currency)
                
                account_balance = income.account_balance
                balance_change = updated_amount_in_uzs - original_amount_in_uzs
                
                account_balance.balance += balance_change
                account_balance.save()
                updated_income.save()
                messages.success(request, 'Income updated successfully.')
                return redirect(f"{reverse('index')}?currency={selected_currency}")
    else:
        form = IncomeForm(instance=income)
    
    income_types = IncomeType.objects.all()
    return render(request, 'history/edit_income.html', {'form': form, 'income_types': income_types, 'income': income, 'currency': selected_currency})

@login_required
def delete_income(request, income_id):
    income = get_object_or_404(Income, id=income_id, account_balance__user=request.user)
    selected_currency = get_selected_currency(request)
    with transaction.atomic():
        account_balance = income.account_balance
        income_amount_in_uzs = convert_to_uzs(income.amount, income.currency)
        account_balance.balance -= income_amount_in_uzs
        account_balance.save()
        income.delete()
        messages.success(request, 'Income deleted successfully.')
    
    return redirect(f"{reverse('index')}?currency={selected_currency}")


@login_required
def history(request):
    selected_currency = get_selected_currency(request)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    expenses = Expense.objects.filter(account_balance__user=request.user)
    incomes = Income.objects.filter(account_balance__user=request.user)

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

############# not enough time to add this function  #############
@login_required
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
                continue

            try:
                date = datetime.strptime(fields[0], '%Y-%m-%d')
                amount = Decimal(fields[1])
                expense_type_name = fields[2]
                manual_expense_type = fields[3] if fields[3] else None
                image = fields[4] if fields[4] else None
                account_balance_id = int(fields[5])

                account_balance = AccountBalance.objects.get(id=account_balance_id, user=request.user)
                expense_type = ExpenseType.objects.get_or_create(name=expense_type_name)[0] if expense_type_name else None

                Expense.objects.create(
                    date=date,
                    amount=amount,
                    expense_type=expense_type,
                    manual_expense_type=manual_expense_type,
                    image=image,
                    account_balance=account_balance
                )
            except Exception as e:
                messages.error(request, f'Error processing line: {line}. Error: {str(e)}')
                continue

        messages.success(request, 'Transactions imported successfully!')
        return redirect(f'history?currency={selected_currency}')

    return render(request, 'history/import.html', {'currency': selected_currency})









############# not enough time to add this function #############
# @login_required
# def add_report(request):
#     selected_currency = get_selected_currency(request)
#     if request.method == 'POST':
#         form = ReportForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Report added successfully.')
#             return redirect(f'index/?currency={selected_currency}')
#     else:
#         form = ReportForm()
#     return render(request, 'history/add_report.html', {'form': form, 'currency': selected_currency})



############# not enough time to add this function  #############
# def export_to_csv(request):
#     selected_currency = get_selected_currency(request)
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = f'attachment; filename=finances_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'

#     writer = csv.writer(response)
#     writer.writerow(['Date', 'Type', 'Amount', 'Currency'])

#     expenses = Expense.objects.filter(account_balance__user=request.user)
#     incomes = Income.objects.filter(account_balance__user=request.user)

#     for expense in expenses:
#         writer.writerow([expense.date, 'Expense', expense.amount, expense.currency])

#     for income in incomes:
#         writer.writerow([income.date, 'Income', income.amount, income.currency])

#     return response
