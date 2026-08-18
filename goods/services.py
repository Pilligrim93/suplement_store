import redis
from carts.services import REDIS_CART_POOL as REDIS_CATALOG_POOL
from django.conf import settings
from goods.models import Product

class CatalogCacheService:
    def __init__(self):
        # Запустили настроенный pool django-redis
        self.redis_client = redis.Redis(connection_pool=REDIS_CATALOG_POOL)


    def write_product_cache(self, product: Product): 

        cache_key = f"catalog:product:{product.id}"

        product_data = {
            "name": product.name,
            "price": product.price,
            "image": product.image.url if product.image else "",
            "quantity": int(product.quantity)
        }
        # Кеширую продукт в redis_cart
        self.redis_client.hset(cache_key, mapping=product_data)


    def write_all_catalog_in_cache(self):
        """
        Полный пакетный разогрев (заливка) всего каталога в Redis при старте сервера.
        Задувает весь прайс-лист в сеть за один укол через высокопроизводительный Pipeline.
        """

        # Обльект с ограниченными полями только те что указали.
        products = Product.objects.only('id', 'name', 'price', 'image', 'quantity')
        if not products:
            return 0
        # transaction=False убираем атомарность так как здесь она не нужна 
        # чтобы другие запросы могли вклиниться так же не задерживаем поток длиной атомарной операцией
        pipe = self.redis_client.pipeline(transaction=False)

        for product in products:
            cache_key = f"catalog:product:{product.id}"
            product_date = {
                "name": product.name,
                "price": int(product.sell_price()),
                "image": product.image.url if product.image else "",
                "quantity": int(product.quantity)
            }
            # Собираем весь список товаров в пакет
            pipe.hset(cache_key, mapping=product_date)
        # Отправка пакета
        pipe.execute()
        return len(products)


