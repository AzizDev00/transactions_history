from django import forms
from .models import Expense, Income, Report, ExpenseType, IncomeType

class ExpenseForm(forms.ModelForm):
    manual_expense_type = forms.CharField(max_length=50, required=False)
    currency = forms.ChoiceField(choices=[
        ('UZS', 'Uzbekistani Som'),
        ('USD', 'US Dollar'),
        ('RUB', 'Russian Rouble')
    ])
    payment_method = forms.ChoiceField(choices=[
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('crypto', 'Crypto')
    ])

    class Meta:
        model = Expense
        fields = ['amount', 'date', 'expense_type', 'manual_expense_type', 'image', 'currency', 'payment_method']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class IncomeForm(forms.ModelForm):
    manual_income_type = forms.CharField(required=False, label='Manual Income Type')
    manual_income_image = forms.ImageField(required=False, label='Image for Manual Income Type')
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    currency = forms.ChoiceField(choices=[
        ('UZS', 'Uzbekistani Som'),
        ('USD', 'US Dollar'),
        ('RUB', 'Russian Rouble')
    ])
    payment_method = forms.ChoiceField(choices=[
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('crypto', 'Crypto')
    ])

    class Meta:
        model = Income
        fields = ['amount', 'income_type', 'manual_income_type', 'manual_income_image', 'image', 'date', 'currency', 'payment_method']

    def clean(self):
        cleaned_data = super().clean()
        income_type = cleaned_data.get('income_type')
        manual_income_type = cleaned_data.get('manual_income_type')

        if not income_type and not manual_income_type:
            raise forms.ValidationError('Please select or enter an income type.')

        return cleaned_data

    

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_type', 'date', 'total_income', 'total_expense']

class ExpenseTypeForm(forms.ModelForm):
    class Meta:
        model = ExpenseType
        fields = ['name']
