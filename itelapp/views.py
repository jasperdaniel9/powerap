import uuid
import requests
import json
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth import authenticate,logout,login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages,auth
from .models import Category, Payment,Product,ShopCart
from .forms import RegisterForm

#Create your views here.

#@login_required(login_url = 'loginpage')
def index(request):
    categories = Category.objects.all()[:3]
    bseller = Product.objects.filter(best_seller= True)
    latest = Product.objects.filter(latest =  True)
    context = {
        'categories' : categories,
        'bseller' : bseller,
        'latest' : latest
    }
    return render(request, "index.html", context)

def categories(request):
    categories = Category.objects.all()

    context = {
        'categories' : categories
    }
    return render(request, 'categories.html',context)

def products(request):
    products = Product.objects.all().filter(available=True)
    categories = Category.objects.all()
    context = {
        'products' : products,
        'categories': categories
    }
    return render(request, 'products.html', context)

def category(request, id):
    category = Product.objects.filter(category_id=id)
    context = {
        'category' : category
    }
    return render(request, 'category.html',context)

def product(request,id):
    product = Product.objects.get(pk=id)
    context = {
        'product' : product
    }
    return render(request, 'product.html', context)

def loginpage(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, 'Login succesful!')
            return redirect('index')
        else:
            messages.success(request, 'Username/Password incorrect')
            return redirect('loginpage')

    return render(request, 'loginpage.html')

def logoutpage(request):
    logout(request)
    messages.success(request, 'Logout succesful')
    return redirect('loginpage')

def registerpage(request):
    regform = RegisterForm()
    if request.method == 'POST':
        regform = RegisterForm(request.POST)
        if regform.is_valid():
            regform.save()
            messages.success(request, 'Signup Successful!')
            return redirect('index')
        else:
            messages.warning(request, regform.errors)
            return redirect('registerpage')

    context = {
        'regform':regform
    }
    return render(request, 'registerpage.html', context)


def password(request):
    update = PasswordChangeForm(request.user)
    if request.method == 'POST':
        update = PasswordChangeForm(request.user, request.POST)
        if update.is_valid():
            user = update.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password update successful')
            return redirect('index')
        else:
            messages.error(request, update.errors)
            return redirect('password')

    context = {
        'update' : update
    }
    return render(request, 'password.html',context)

@login_required(login_url='loginpage')
def addtocart(request):
    if request.method == 'POST':
        basket_code = str(uuid.uuid4())
        vol = int(request.POST['itemquant'])
        pid = request.POST['itemid']
        itemid= Product.objects.get(pk=pid)
        cart = ShopCart.objects.filter(user__username= request.user.username, paid_item=False)
        if cart:
            basket = ShopCart.objects.filter(product_id = itemid.id ,user__username= request.user.username ).first()
            if basket:
                basket.quantity += vol
                basket.save()
                messages.success(request, 'Products added to Basket!')
                return redirect('products')
            else:
                newitem = ShopCart()
                newitem.user = request.user
                newitem.product = itemid
                newitem.quantity = vol
                newitem.paid_item = False
                newitem.cart_no = cart[0].cart_no
                newitem.save()
        else:
            newbasket = ShopCart()
            newbasket.user = request.user
            newbasket.product = itemid
            newbasket.quantity = vol
            newbasket.paid_item = False
            newbasket.cart_no = basket_code
            newbasket.save()
            messages.success(request, 'Product added to Basket!')
        return redirect('products')
    #return HttpResponse('addtocart')

@login_required(login_url='loginpage')
def cart(request):
    basket = ShopCart.objects.filter(user__username= request.user.username, paid_item=False )
     
    
     
    subtotal = 0
    vat = 0
    total = 0

    for item in basket:
        subtotal += item.product.price * item.quantity

    vat = 0.075 * subtotal

    total = subtotal + vat

    context ={
        'basket': basket,
        'subtotal' :subtotal,
        'vat':vat,
        'total':total,
        
    }
    return render(request, 'cart.html',context)


def deleteitem(request):
    remove = request.POST['delitem']
    ShopCart.objects.filter(pk=remove).delete()
    messages.success(request, 'Item successfully deleted!')
    return redirect('cart')


def updatequant(request):
    add = request.POST['additem']
    addid = request.POST['itemid']
    adjust = ShopCart.objects.get(pk=addid)
    adjust.quantity = add
    adjust.save()
    messages.success(request, 'Item quantity has been updated')
    return redirect('cart')

   

def checkout(request):
    basket = ShopCart.objects.filter(user__username= request.user.username, paid_item=False )

    subtotal = 0
    vat = 0
    total = 0

    for item in basket:
        subtotal += item.product.price * item.quantity

    vat = 0.075 * subtotal

    total = subtotal + vat

    context = {
        'basket': basket,
        'total':total,
        'order_code': basket[0].cart_no
    }
    
    return render(request, 'checkout.html',context)


@login_required(login_url='loginpage')
def sendorder(request):
    if request.method == 'POST':
        api_key = 'sk_test_f0a5a8b92ea759bd42326fce0253c74bf3fc8ac9'
        curl= 'https://api.paystack.co/transaction/initialize'
        #cburl = 'http://127.0.0.1:8000/completed'
        cburl = 'http://3.144.168.70/completed'
        price = float(request.POST['price']) * 100
        bag_num = request.POST['bag']
        user = User.objects.get(username = request.user.username)
        pay_num = str(uuid.uuid4())
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        phone = request.POST['phone']
        address = request.POST['address']
        state = request.POST['state']
        
        headers = {'Authorization': f'Bearer {api_key}'}
        data = {
            'reference' : pay_num,
            'amount' : int(price),
            'order_number' : bag_num,
            'email' : user.email,
            'callback_url' : cburl
        }        

        try:
            r = requests.post(curl, headers=headers,json=data) 
        except Exception:
            messages.error(request, 'Network busy, try again')
        else:
            transback = json.loads(r.text)
            rd_url = transback['data']['authorization_url']

            paid = Payment()
            paid.user = user
            paid.paid_item = True
            paid.cart_no = bag_num
            paid.pay_code = pay_num
            paid.total = price
            paid.first_name = first_name
            paid.last_name = last_name
            paid.phone = phone
            paid.address = address
            paid.state = state
            paid.save()

            bag = ShopCart.objects.filter(user__username= request.user.username, paid_item=False )
            for item in bag:
                item.paid_item = True
                item.save()

                new_quantity = Product.objects.get(pk= item.product.id)
                new_quantity.max_quant -= item.quantity
                new_quantity.save()

            return redirect(rd_url)
    return redirect('checkout')
    


@login_required(login_url='loginpage')
def completed(request):
    user = User.objects.get(username= request.user.username)
    context = {
         'user':user
     }
    return render(request, 'completed.html')