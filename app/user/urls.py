# app/user/urls.py
from django.urls import path

# Import our views
from user import views

# Define our app name to help ID which app we're creating the URL from
# when we use our reverse()
app_name = 'user'

# Create our urlpatterns. We want the path to be user/create to create a user
# Then the view we want to wire this URL up to
urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('me/', views.ManageUserView.as_view(), name='me'),
]
