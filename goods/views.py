from django.shortcuts import get_object_or_404, render

from goods.models import Product



def shop(request):
    products = Product.objects.all()

    context = {
        'products': products
    }
    return render(request, "shop.html", context)



def shop_single(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, "shop-single.html", {'product': product})


# def shop_single(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     return render(request, "shop-single.html", {'product': product})

def cart(request):
    return render(request, "cart.html")



def checkout(request):
    return render(request, "checkout.html")


def thankyou(request):
    return render(request, "thankyou.html")
