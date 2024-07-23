# views.py
import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AccountBalance, Expense, ExpenseType, Income, IncomeType, Report
from .forms import ExpenseForm, IncomeForm, ReportForm, ExpenseTypeForm
from datetime import datetime

def index(request):
    expenses = Expense.objects.all()
    incomes = Income.objects.all()
    
    total_expenses = sum(expense.amount for expense in expenses)
    total_incomes = sum(income.amount for income in incomes)

    context = {
        'expenses': expenses,
        'incomes': incomes,
        'total_expenses': total_expenses,
        'total_incomes': total_incomes,
        'balance': total_incomes - total_expenses
    }
    return render(request, 'history/index.html', context)

@login_required
def add_expense(request):
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
                return render(request, 'history/add_expense.html', {'form': form, 'expense_types': ExpenseType.objects.all()})

            account_balance, created = AccountBalance.objects.get_or_create(user=request.user)
            if account_balance.balance >= expense.amount:
                expense.account_balance = account_balance
                account_balance.balance -= expense.amount
                account_balance.save()
                expense.save()
                messages.success(request, 'Expense added successfully.')
                return redirect('index')
            else:
                messages.error(request, 'You do not have enough funds in your account.')
    else:
        form = ExpenseForm()

    expense_types = ExpenseType.objects.all()
    return render(request, 'history/add_expense.html', {'form': form, 'expense_types': expense_types})

@login_required
def add_income(request):
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

            income.account_balance = AccountBalance.objects.get_or_create(user=request.user)[0]
            income.account_balance.balance += income.amount
            income.account_balance.save()
            income.save()
            messages.success(request, 'Income added successfully.')
            return redirect('index')
        else:
            messages.error(request, 'There was an error with your form.')
    else:
        form = IncomeForm()

    income_types = IncomeType.objects.all()
    return render(request, 'history/add_income.html', {'form': form, 'income_types': income_types})

@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    old_amount = expense.amount
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            new_expense = form.save(commit=False)
            account_balance = expense.account_balance
            new_balance = account_balance.balance + old_amount - new_expense.amount
            if new_balance >= 0:
                account_balance.balance = new_balance
                account_balance.save()
                new_expense.save()
                return redirect('index')
            else:
                messages.error(request, 'You do not have enough funds in your account.')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'history/edit_expense.html', {'form': form})

@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        account_balance = expense.account_balance
        account_balance.balance += expense.amount
        account_balance.save()
        expense.delete()
        messages.success(request, 'Expense deleted successfully.')
        return redirect('index')
    return render(request, 'history/delete_expense.html', {'expense': expense})

@login_required
def edit_income(request, pk):
    income = get_object_or_404(Income, pk=pk)
    old_amount = income.amount
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            new_income = form.save(commit=False)
            account_balance = income.account_balance
            account_balance.balance -= old_amount
            account_balance.balance += new_income.amount
            account_balance.save()
            new_income.save()
            messages.success(request, 'Income updated successfully.')
            return redirect('index')
    else:
        form = IncomeForm(instance=income)
    return render(request, 'history/edit_income.html', {'form': form})

@login_required
def delete_income(request, pk):
    income = get_object_or_404(Income, pk=pk)
    if request.method == 'POST':
        account_balance = income.account_balance
        account_balance.balance -= income.amount
        account_balance.save()
        income.delete()
        messages.success(request, 'Income deleted successfully.')
        return redirect('index')
    return render(request, 'history/delete_income.html', {'income': income})

@login_required
def add_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Report added successfully.')
            return redirect('index')
    else:
        form = ReportForm()
    return render(request, 'history/add_report.html', {'form': form})

@login_required
def add_expense_type(request):
    if request.method == 'POST':
        form = ExpenseTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense type added successfully.')
            return redirect('index')
    else:
        form = ExpenseTypeForm()
    return render(request, 'history/add_expense_type.html', {'form': form})

@login_required
def history(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        expenses = Expense.objects.filter(date__range=(start_date, end_date))
        incomes = Income.objects.filter(date__range=(start_date, end_date))
    else:
        expenses = Expense.objects.all()
        incomes = Income.objects.all()

    total_expenses = sum(expense.amount for expense in expenses)
    total_incomes = sum(income.amount for income in incomes)
    account_balance, created = AccountBalance.objects.get_or_create(user=request.user)

    context = {
        'expenses': expenses,
        'incomes': incomes,
        'total_expenses': total_expenses,
        'total_incomes': total_incomes,
        'balance': account_balance.balance,
    }

    return render(request, 'history/history.html', context)

def import_transactions(request):
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
        return redirect('history')

    return render(request, 'history/import.html')