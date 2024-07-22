from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AccountBalance, Expense, ExpenseType, Income, Report
from .forms import ExpenseForm, IncomeForm, ReportForm, ExpenseTypeForm
from django.utils import timezone
from datetime import datetime

@login_required
def index(request):
    expenses = Expense.objects.filter(account_balance__user=request.user)
    incomes = Income.objects.filter(account_balance__user=request.user)
    account_balance, created = AccountBalance.objects.get_or_create(user=request.user)
    return render(request, 'history/index.html', {
        'expenses': expenses,
        'incomes': incomes,
        'balance': account_balance.balance,
    })

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.date = form.cleaned_data['date']
            account_balance, created = AccountBalance.objects.get_or_create(user=request.user)
            if account_balance.balance >= expense.amount:
                expense.account_balance = account_balance
                account_balance.balance -= expense.amount
                account_balance.save()
                expense.save()
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
            account_balance, created = AccountBalance.objects.get_or_create(user=request.user)
            income.account_balance = account_balance
            account_balance.balance += income.amount
            account_balance.save()
            income.save()
            messages.success(request, 'Income added successfully.')
            return redirect('index')
    else:
        form = IncomeForm()
    return render(request, 'history/add_income.html', {'form': form})

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
            account_balance.balance -= old_amount  # Subtract the old amount
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
        'balance': account_balance.balance,  # Use balance from AccountBalance model
    }

    return render(request, 'history/history.html', context)
