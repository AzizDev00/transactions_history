from django import forms
from .models import Expense, Income, Report, ExpenseType
from django.utils import timezone


class ExpenseForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), initial=timezone.now)

    class Meta:
        model = Expense
        fields = ['amount', 'date', 'expense_type', 'image']

class IncomeForm(forms.ModelForm):
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), initial=timezone.now)

    class Meta:
        model = Income
        fields = ['amount', 'date', 'income_type', 'image']
    
class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_type', 'date', 'total_income', 'total_expense']

class ExpenseTypeForm(forms.ModelForm):
    class Meta:
        model = ExpenseType
        fields = ['name']
