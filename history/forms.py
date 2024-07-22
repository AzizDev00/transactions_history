from django import forms
from .models import Expense, Income, Report, ExpenseType
from django.utils import timezone

class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}))

class ExpenseForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Expense
        fields = ['amount', 'expense_type', 'image', 'date']

class IncomeForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Income
        fields = ['amount', 'income_type', 'image', 'date']
    
class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_type', 'date', 'total_income', 'total_expense']

class ExpenseTypeForm(forms.ModelForm):
    class Meta:
        model = ExpenseType
        fields = ['name']
