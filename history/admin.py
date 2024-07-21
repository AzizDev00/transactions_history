from django.contrib import admin
from .models import ExpenseType, IncomeType, AccountBalance, Expense, Income

admin.site.register(ExpenseType)
admin.site.register(IncomeType)
admin.site.register(AccountBalance)
admin.site.register(Expense)
admin.site.register(Income)
