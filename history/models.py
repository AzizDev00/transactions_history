from django.db import models

from users.models import User

class AccountBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s balance: {self.balance}"
    
class ExpenseType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class IncomeType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    account_balance = models.ForeignKey(AccountBalance, on_delete=models.CASCADE)
    expense_type = models.CharField(max_length=50)
    image = models.ImageField(upload_to='expense_images/', blank=True, null=True)

    def __str__(self):
        return f'{self.amount} - {self.date}'

class Income(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    account_balance = models.ForeignKey(AccountBalance, on_delete=models.CASCADE)
    income_type = models.ForeignKey(IncomeType, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='income_images/', blank=True, null=True)

    def __str__(self):
        return f'{self.amount} - {self.date}'
    
    
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

