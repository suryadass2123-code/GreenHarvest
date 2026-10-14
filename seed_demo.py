from django.contrib.auth.models import User
from accounts.models import Profile
from products.models import Category, Product
from orders.models import Coupon

categories = ['Fruits', 'Vegetables', 'Leafy Greens', 'Grains', 'Spices', 'Dairy']
for name in categories:
    Category.objects.get_or_create(name=name)

farmer, _ = User.objects.get_or_create(username='demo_farmer', defaults={'first_name':'Demo','last_name':'Farmer','email':'farmer@example.com'})
farmer.set_password('Farmer@123')
farmer.save()
Profile.objects.get_or_create(user=farmer, defaults={'role':'farmer'})

customer, _ = User.objects.get_or_create(username='demo_customer', defaults={'first_name':'Demo','last_name':'Customer','email':'customer@example.com'})
customer.set_password('Customer@123')
customer.save()
Profile.objects.get_or_create(user=customer, defaults={'role':'customer'})

veg = Category.objects.get(name='Vegetables')
Product.objects.get_or_create(farmer=farmer, name='Fresh Tomato', defaults={'category':veg,'description':'Farm-fresh tomato','price':40,'stock':50,'unit':'kg','location':'Dindigul'})
Product.objects.get_or_create(farmer=farmer, name='Fresh Potato', defaults={'category':veg,'description':'Fresh local potato','price':50,'stock':30,'unit':'kg','location':'Dindigul'})
Coupon.objects.get_or_create(code='WELCOME10', defaults={'description':'10% off','discount_type':'PERCENT','discount_value':10,'minimum_amount':300,'maximum_discount':100,'active':True})
print('Demo data created. Farmer: demo_farmer / Farmer@123 | Customer: demo_customer / Customer@123')
