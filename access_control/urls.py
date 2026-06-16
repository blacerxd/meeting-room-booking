from django.urls import path
from . import views

app_name = 'access'

urlpatterns = [
    path('policies/', views.policies_list, name='policies_list'),
    path('assign/', views.assign_policy, name='assign_policy'),

]
