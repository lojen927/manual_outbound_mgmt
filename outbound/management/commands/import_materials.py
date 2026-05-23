import os
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import DataError

import openpyxl

from outbound.models import Material


# 常见表头名称映射
HEADER_ALIASES = {
    'material_code': ['物料编码', '编码', '物料代码', '代码', 'code', 'material code', '物料号', '料号'],
    'material_name': ['物料描述', '描述', '物料名称', '名称', 'name', 'material name', '品名'],
    'specification': ['规格', '规格型号', '型号', 'spec', 'specification'],
    'unit': ['单位', '计量单位', '基本单位', 'unit', '单位名称'],
}


def detect_headers(headers):
    """根据表头行自动匹配各列索引"""
    mapping = {}
    for col_idx, header in enumerate(headers):
        header_clean = str(header).strip().lower()
        for field, aliases in HEADER_ALIASES.items():
            if any(a.lower() == header_clean or a.lower() in header_clean for a in aliases):
                mapping[field] = col_idx
                break
    return mapping


class Command(BaseCommand):
    help = '从 Excel 文件导入物料数据到 Material 表'

    def add_arguments(self, parser):
        parser.add_argument('file', help='Excel 文件路径（.xlsx）')
        parser.add_argument(
            '--sheet', default=None,
            help='工作表名称（默认使用活动工作表）',
        )
        parser.add_argument(
            '--batch-size', type=int, default=2000,
            help='批量写入每批条数（默认 2000）',
        )
        parser.add_argument(
            '--clear', action='store_true',
            help='导入前清空已有物料数据',
        )

    def handle(self, *args, **options):
        file_path = options['file']

        if not os.path.isfile(file_path):
            raise CommandError(f'文件不存在: {file_path}')

        if options['clear']:
            self.stdout.write('正在清空已有物料数据…')
            deleted, _ = Material.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'已删除 {deleted} 条记录'))

        self.stdout.write(f'正在读取: {file_path}')
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)

        ws = wb[options['sheet']] if options['sheet'] else wb.active
        rows_iter = ws.iter_rows(values_only=True)

        # 读取表头
        try:
            header_row = next(rows_iter)
        except StopIteration:
            raise CommandError('Excel 文件为空')

        mapping = detect_headers(header_row)
        missing = [f for f in ['material_code', 'material_name'] if f not in mapping]
        if missing:
            actual_headers = [str(h) for h in header_row if h is not None]
            raise CommandError(
                f'表头中未找到物料编码或物料描述列。\n'
                f'检测到的表头: {actual_headers}\n'
                f'支持的列名: {HEADER_ALIASES}'
            )

        self.stdout.write(f'列映射: {mapping}')
        self.stdout.write('正在导入…')

        batch = []
        total = 0
        errors = 0
        start_ts = time.time()

        for row_idx, row in enumerate(rows_iter, 2):
            code = str(row[mapping['material_code']]).strip() if row[mapping['material_code']] is not None else ''
            name = str(row[mapping['material_name']]).strip() if row[mapping['material_name']] is not None else ''

            if not code or not name:
                continue

            spec = ''
            if 'specification' in mapping and row[mapping['specification']] is not None:
                spec = str(row[mapping['specification']]).strip()

            unit = ''
            if 'unit' in mapping and row[mapping['unit']] is not None:
                unit = str(row[mapping['unit']]).strip()

            batch.append(Material(
                material_code=code,
                material_name=name,
                specification=spec,
                unit=unit,
            ))
            total += 1

            if len(batch) >= options['batch_size']:
                try:
                    Material.objects.bulk_create(batch, ignore_conflicts=True)
                except DataError as e:
                    errors += 1
                    self.stderr.write(self.style.ERROR(f'第 {row_idx} 行附近写入出错: {e}'))
                batch = []
                elapsed = time.time() - start_ts
                rate = total / elapsed if elapsed > 0 else 0
                self.stdout.write(f'  已处理 {total} 条… ({rate:.0f} 条/秒)')

        # 写入剩余批次
        if batch:
            try:
                Material.objects.bulk_create(batch, ignore_conflicts=True)
            except DataError as e:
                errors += 1
                self.stderr.write(self.style.ERROR(f'写入出错: {e}'))

        elapsed = time.time() - start_ts
        count = Material.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\n导入完成!\n'
            f'  读取总计: {total} 行\n'
            f'  数据库中现有: {count} 条\n'
            f'  写入错误: {errors}\n'
            f'  耗时: {elapsed:.1f} 秒'
        ))
