from django.core.management.base import BaseCommand
from django.utils import timezone

from outbound.models import ManualOutboundOrder


class Command(BaseCommand):
    help = '删除所有草稿状态的出库单'

    def handle(self, *args, **options):
        drafts = ManualOutboundOrder.objects.filter(status='draft')
        count = drafts.count()
        if count == 0:
            self.stdout.write('没有需要清理的草稿出库单。')
            return
        drafts.delete()
        self.stdout.write(self.style.SUCCESS(f'已删除 {count} 条草稿出库单。'))
