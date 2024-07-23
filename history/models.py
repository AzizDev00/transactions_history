from django.db import models
from users.models import User

class AccountBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s balance: {self.balance}"

class ExpenseType(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='expense_types/')

    def __str__(self):
        return self.name

class IncomeType(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='income_types/', null=True, blank=True)

    def __str__(self):
        return self.name


class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    account_balance = models.ForeignKey(AccountBalance, on_delete=models.CASCADE)
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.SET_NULL, null=True, blank=True)
    manual_expense_type = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(upload_to='expense_images/', blank=True, null=True)

    def __str__(self):
        return f'{self.amount} - {self.date}'

class Income(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    income_type = models.ForeignKey(IncomeType, on_delete=models.SET_NULL, null=True, blank=True)
    manual_income_type = models.CharField(max_length=255, null=True, blank=True)
    manual_income_image = models.ImageField(upload_to='manual_income_types/', null=True, blank=True)
    image = models.ImageField(upload_to='incomes/', null=True, blank=True)
    date = models.DateField()
    account_balance = models.ForeignKey(AccountBalance, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.amount} - {self.income_type or self.manual_income_type}'

class Report(models.Model):
    REPORT_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    report_type = models.CharField(max_length=10, choices=REPORT_CHOICES)
    date = models.DateField()
    total_income = models.DecimalField(max_digits=10, decimal_places=2)
    total_expense = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.report_type} - {self.date}'