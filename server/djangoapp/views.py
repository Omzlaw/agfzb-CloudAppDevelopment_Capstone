from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, get_dealer_by_id_from_cf, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)

# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html', context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/login.html', context)
    else:
        # Get username and password from request.POST dictionary
        username = request.POST['username']
        password = request.POST['password']
        # Try to check if provide credential can be authenticated
        user = authenticate(username=username, password=password)
        if user is not None:
            # If user is valid, call login method to login current user
            login(request, user)
            return redirect('djangoapp:index')
        else:
            # If not, return to login page again
            return render(request, 'djangoapp/login.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    # Logout user in the request
    logout(request)
    # Redirect user back to index view
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    # If it is a GET request, just render the registration page
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    # If it is a POST request
    elif request.method == 'POST':
        # Get user information from request.POST
        username = request.POST['username']
        password = request.POST['password']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            # Check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            # If not, simply log this is a new user
            logger.debug("{} is new user".format(username))
        # If it is a new user
        if not user_exist:
            # Create user in auth_user table
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # Login the user and redirect to course list page
            login(request, user)
            return redirect("djangoapp:index")
        else:
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
# def get_dealerships(request):
    # context = {}
    # if request.method == "GET":
    #     return render(request, 'djangoapp/index.html', context)

def get_dealerships(request):
    context = {}
    if request.method == "GET":
        url = "https://us-south.functions.cloud.ibm.com/api/v1/web/816ebcf6-e6db-4799-95d8-8ce28f6078c8/dealership-package/get-dealership.json"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        # Concat all dealer's short name
        # dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        context['dealership_list'] = dealerships
        # Return a list of dealer short name
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == "GET":
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/816ebcf6-e6db-4799-95d8-8ce28f6078c8/dealership-package/get-dealership-reviews.json"
        # Get dealer details from the URL
        dealer_reviews = get_dealer_reviews_from_cf(url, dealer_id)


        url_2 = "https://us-south.functions.appdomain.cloud/api/v1/web/816ebcf6-e6db-4799-95d8-8ce28f6078c8/dealership-package/get-dealership-by-id.json"
        # Get dealer details from the URL
        dealer_details = get_dealer_by_id_from_cf(url_2, dealer_id)

        context['dealership_reviews_list'] = dealer_reviews
        context['dealer_id'] = dealer_id
        context['dealer_details'] = dealer_details

        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    context = {}
    if request.user.is_authenticated:
        if request.method == "GET":
            url_2 = "https://us-south.functions.appdomain.cloud/api/v1/web/816ebcf6-e6db-4799-95d8-8ce28f6078c8/dealership-package/get-dealership-by-id.json"
            # Get dealer details from the URL
            dealer_details = get_dealer_by_id_from_cf(url_2, dealer_id)

            context['dealer_id'] = dealer_id
            context['dealer_details'] = dealer_details
            context['cars'] = CarModel.objects.all()
            return render(request, 'djangoapp/add_review.html', context)

        current_user = request.user
        user_names = ""

        if(current_user.first_name):
            user_names = f"{current_user.first_name} {current_user.last_name}"
        else:
            user_names = current_user.username
            
        car_model = CarModel.objects.get(id=request.POST["car"])
        car_model_name = car_model.name
        car_model_year = car_model.year.strftime("%Y")
        car_make = car_model.car_make.name

        purchase_check = False
        if("purchasecheck" in request.POST):
            purchase_check = True

        review = {
            "id": 1000,
            "name": user_names,
            "dealership": int(dealer_id),
            "review": request.POST["content"],
            "purchase": purchase_check,
            "purchase_date": request.POST["purchasedate"],
            "car_make": car_make,
            "car_model": car_model_name,
            "car_year": car_model_year
        }
        json_payload = {
            "review": review
        }

        url = "https://us-south.functions.appdomain.cloud/api/v1/web/816ebcf6-e6db-4799-95d8-8ce28f6078c8/dealership-package/add-review.json"

        response = post_request(url, json_payload), 

        return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
    else:
        # User is not authenticated, you may want to redirect them to a login page
       return redirect("djangoapp:login")


