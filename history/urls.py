from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('add_expense/', views.add_expense, name='add_expense'),
    path('edit_expense/<int:pk>/', views.edit_expense, name='edit_expense'),
    path('delete_expense/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('add_income/', views.add_income, name='add_income'),
    path('edit_income/<int:pk>/', views.edit_income, name='edit_income'),
    path('delete_income/<int:pk>/', views.delete_income, name='delete_income'),
    path('add_report/', views.add_report, name='add_report'),
    path('add_expense_type/', views.add_expense_type, name='add_expense_type'),
    path('history/', views.history, name='history'),

]
