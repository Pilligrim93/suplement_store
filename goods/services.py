import redis
from carts.services import REDIS_CATALOG_POOL
from django.conf import settings
from goods.models import Product

class CatalogCacheService:
    def __init__(self):
        # Запустили настроенный pool django-redis 4
        self.redis_client_catalog = redis.Redis(connection_pool=REDIS_CATALOG_POOL)


    def write_product_cache(self, product: Product): 
        """Запись одного продукта в кеш"""

        cache_key = f"catalog:product:{product.id}"

        product_data = {
            "name": product.name,
            "price": int(product.sell_price()),
            "image": product.image.url if product.image else "",
            "quantity": int(product.quantity)
        }
        # Кеширую продукт в redis_catalog 4
        self.redis_client_catalog.hset(cache_key, mapping=product_data)


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
        pipe = self.redis_client_catalog.pipeline(transaction=False)

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


    def write_products_batch_in_cache(self, product_ids: list[int]) -> int:
        """
        Высокопроизводительная запись измененных нескольких товаров ПАЧКАМИ (по 50-100 шт).
        Идеальный баланс: 1 легкий SQL-запрос в СУБД и 1 Pipeline-укол в Redis 4 инстанса.
        """
        # Выкачиваем пачку строго по списку ID и только нужные поля
        # id__in - получаем все товары на этот момент
        products = Product.objects.filter(id__in=product_ids).only('id', 'name', 'price', 'image', 'quantity')

        if not products:
            return 0
        pipe = self.redis_client_catalog.pipeline(transaction=False)

        for product in products:
            cache_key = f"catalog:product:{product.id}"
            product_data = {
                "name": product.name,
                "price": int(product.sell_price()),
                "image": product.image.url if product.image else "",
                "quantity": int(product.quantity)
            }
            pipe.hset(cache_key, mapping=product_data)

        pipe.execute()
        return len(products)


# Наполтить наш кеш каталог товарами.