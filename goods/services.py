
import re
import logging
from typing import Optional, List, Dict, Any
import redis
from redis.commands.search.query import Query
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.field import TextField, TagField, NumericField
from goods.models import Product
from carts.services import REDIS_CATALOG_POOL

logger = logging.getLogger(__name__)


class CatalogCacheService:
    """
    Enterprise-сервис для денормализации, атомарного прогрева и сквозного
    высокоскоростного поиска по каталогу товаров через движок RediSearch.
    """

    def __init__(self) -> None:
        
        self.redis_client = redis.Redis(connection_pool=REDIS_CATALOG_POOL)
        self.index_name = "idx:catalog"
        self.key_prefix = "catalog:product:"
        
        # Предкомпилированное регулярное выражение для мгновенного экранирования спецсимволов RediSearch
        self._rs_escape_re = re.compile(r"[,.<>\{\}\[\]\"':;!@#\$%\^\&\*\(\)\-\+\=\~\| ]")

    def _prepare_product_data(self, product: Product) -> Dict[str, str]:
        """
        Инструмент денормализации. Гарантирует строгость структуры кэша.
        Все значения приводятся к строкам для безопасного хранения в Redis HASH.
        """
        try:
            image_url = product.image.url if product.image else ""
        except (ValueError, AttributeError):
            image_url = ""

        return {
            "id": str(product.id),
            "name": product.name,
            "slug": product.slug,
            "category_name": product.category.name if product.category else "Без категории",
            "description": product.description or "",
            "price": str(int(product.sell_price())),
            "discount": str(int(product.discount)),
            "quantity": str(int(product.quantity)),
            "image": image_url
        }

    def _escape_string(self, text: Optional[str]) -> str:
        """Безопасное экранирование служебных символов RediSearch."""
        if not text or not text.strip():
            return ""
        return self._rs_escape_re.sub(r"\\\g<0>", text.strip())

    # ==============================================================================
    # УПРАВЛЕНИЕ ИНДЕКСОМ И ЗАПИСЬ (Write Path)
    # ==============================================================================

    def check_or_create_index(self) -> None:
        """Декларативная проверка и автоматическое создание индекса RediSearch."""
        search_index = self.redis_client.ft(self.index_name)
        try:
            search_index.info()
        except redis.exceptions.ResponseError:
            logger.info(f"[RediSearch] Создание индекса {self.index_name}...")
            schema = (
                TextField("name", sortable=True),
                TagField("category_name", sortable=True),
                NumericField("price", sortable=True),
                NumericField("discount", sortable=True)
            )
            definition = IndexDefinition(index_type=IndexType.HASH, prefix=[self.key_prefix])
            search_index.create_index(fields=schema, definition=definition)

    def write_product_cache(self, product: Product) -> None:
        """Запись или обновление одного продукта в кэше (O(1))."""
        cache_key = f"{self.key_prefix}{product.slug}"
        product_data = self._prepare_product_data(product)
        self.redis_client.hset(cache_key, mapping=product_data)

    def write_products_batch_in_cache(self, product_ids: List[int]) -> int:
        """Высокопроизводительная пакетная запись измененных товаров (Celery-конвейер)."""
        if not product_ids:
            return 0

        products = Product.objects.filter(id__in=product_ids).select_related('category').only(
            'id', 'name', 'slug', 'category__name', 'description', 'discount', 'quantity', 'image'
        )

        pipe = self.redis_client.pipeline(transaction=False)
        counter = 0

        for product in products:
            cache_key = f"{self.key_prefix}{product.slug}"
            pipe.hset(cache_key, mapping=self._prepare_product_data(product))
            counter += 1

        if counter > 0:
            pipe.execute()
        return counter

    def write_all_catalog_in_cache(self) -> int:
        """Тотальный пакетный разогрев всего каталога (Защищен от OOM)."""
        products = Product.objects.filter(quantity__gt=0).select_related('category').only(
            'id', 'name', 'slug', 'category__name', 'description', 'discount', 'quantity', 'image'
        )

        # Асинхронный сброс текущей DB на стороне Redis без блокировки single-thread ядра
        self.redis_client.flushdb(asynchronous=True)
        # Гарантируем, что индекс пересоздастся сразу после очистки базы
        self.check_or_create_index()

        pipe = self.redis_client.pipeline(transaction=False)
        counter = 0
        chunk_size = 2000

        for product in products.iterator(chunk_size=chunk_size):
            cache_key = f"{self.key_prefix}{product.slug}"
            pipe.hset(cache_key, mapping=self._prepare_product_data(product))
            counter += 1

            if counter % chunk_size == 0:
                pipe.execute()

        if counter % chunk_size != 0:
            pipe.execute()

        if counter == 0:
            logger.warning("⚠️ [Warmup] База данных PostgreSQL пуста.")
        else:
            logger.info(f"🚀 [Warmup] Успешно прогрето {counter} товаров.")
        return counter

    # ==============================================================================
    # ПОИСК И ЧТЕНИЕ (Read Path)
    # ==============================================================================

    def get_cached_catalog_for_shop(
        self, 
        category_name: Optional[str] = None, 
        search_query: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        has_discount: bool = False,
        sort_by: Optional[str] = None,  # 'price_asc', 'price_desc', 'discount', 'alphabet'
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Универсальный полнотекстовый поиск, фильтрация по диапазонам цен/скидок 
        и сортировка каталога порциями через объектный Query Builder RediSearch.
        """
        # 1. Полнотекстовый поиск (логика AND по словам)
        if search_query and search_query.strip():
            clean_query = self._escape_string(search_query)
            query_string = " ".join([w for w in clean_query.split() if w])
        else:
            query_string = "*"

        # 2. Фильтрация по TAG-полю категории
        if category_name and category_name.strip():
            query_string += f" @category_name:{{{self._escape_string(category_name)}}}"

        # 3. Фильтрация по NUMERIC-диапазонам цены
        if min_price is not None or max_price is not None:
            low = min_price if min_price is not None else 0
            high = max_price if max_price is not None else "+inf"
            query_string += f" @price:[{low} {high}]"

        # 4. Фильтрация товаров только со скидкой
        if has_discount:
            query_string += " @discount:[1 +inf]"

        # 5. Сборка объекта запроса и проекция полей (экономия сети за счет урезания description)
        offset = (page - 1) * page_size
        query = Query(query_string).paging(offset, page_size)
        query.return_fields("id", "name", "slug", "category_name", "price", "discount", "image")

        # 6. Применение сортировки на стороне ядра Redis C-level
        if sort_by:
            sort_mappings = {
                "price_asc": ("price", True),
                "price_desc": ("price", False),
                "discount": ("discount", False),
                "alphabet": ("name", True)
            }
            if sort_data := sort_mappings.get(sort_by):
                query.sort_by(sort_data[0], ascii=sort_data[1])

        try:
            search_results = self.redis_client.ft(self.index_name).search(query)
        except redis.exceptions.ResponseError as e:
            logger.error("[RediSearch] Ошибка выполнения запроса: %s", e)
            return {"total": 0, "products": []}

        if not search_results or search_results.total == 0:
            return {"total": 0, "products": []}

        # 7. Zero-copy маппинг результатов в список
        return {
            "total": search_results.total,
            "products": [
                {
                    "id": int(getattr(doc, "id", 0)),
                    "name": getattr(doc, "name", ""),
                    "slug": getattr(doc, "slug", ""),
                    "category_name": getattr(doc, "category_name", ""),
                    "price": int(getattr(doc, "price", 0)),
                    "discount": int(getattr(doc, "discount", 0)),
                    "image": getattr(doc, "image", "")
                }
                for doc in search_results.docs
            ]
        }

    def get_cached_product_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Получение детальной информации о товаре для карточки Single View."""
        cache_key = f"{self.key_prefix}{slug}"
        raw_data = self.redis_client.hgetall(cache_key)

        if not raw_data:
            return None

        return {
            "id": int(raw_data.get("id", 0)),
            "name": raw_data.get("name"),
            "slug": raw_data.get("slug"),
            "category_name": raw_data.get("category_name"),
            "description": raw_data.get("description"),
            "price": int(raw_data.get("price", 0)),
            "discount": int(raw_data.get("discount", 0)),
            "quantity": int(raw_data.get("quantity", 0)),
            "image": raw_data.get("image", "")
        }






# Дорабоать сервис должен быть поиск по разныим фильтрам категории слаг цена скидки и тд
# Провести код ревью!