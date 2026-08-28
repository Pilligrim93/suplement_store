from django.core.management.base import BaseCommand

class Command(BaseCommand):

    help = "Высоконагруженный разовый прогрев кэша всего каталога товаров в (Инстанс 4)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("[Warmup] Инициализация прогрева каталога..."))

        try:
            # Скрытый импорт таски внутри метода handle для защиты от Circular Imports!
            from goods.tasks import task_write_all_catalog_in_cache

            # Отправляю задачу в 3-й инстанс брокера (порт 6381)
            task_write_all_catalog_in_cache.delay()

            self.stdout.write(
                self.style.SUCCESS("[Warmup] Задача полной заливки каталога успешно передана в Celery!")
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"[Warmup] Критический сбой при отправке задачи: {e}")
            )

