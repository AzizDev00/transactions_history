from django.urls import path
from . import views



urlpatterns = [
    path('', views.index, name='index'),
    path('add_expense/', views.add_expense, name='add_expense'),
    path('edit_expense/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('delete_expense/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    path('add_income/', views.add_income, name='add_income'),
    path('edit_income/<int:income_id>/', views.edit_income, name='edit_income'),
    path('delete_income/<int:income_id>/', views.delete_income, name='delete_income'),
    path('history/', views.history, name='history'),
    # path('add_report/', views.add_report, name='add_report'),  ############# not enough time to add this function  #############
    # path('import/', views.import_transactions, name='import_transactions'), ############# not enough time to add this function  #############
]
