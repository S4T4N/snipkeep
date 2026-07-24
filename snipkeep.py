#!/usr/bin/env python3
# snipkeep.py - بنك المقتطفات الذكي

import sys
import argparse
from pathlib import Path

from core.snip_indexer import SnipIndexer
from core.engine import SearchEngine
from core.sandbox import Sandbox
from utils.helpers import copy_to_clipboard

# نؤجل تحميل rich حتى نحتاجه فعلاً
def print_banner():
    print("""
╔══════════════════════════════════════╗
║        🧠  SnipKeep v1.0.0         ║
║   بنك المقتطفات الذكي بالمعنى      ║
╚══════════════════════════════════════╝
    """)

def cmd_add(args):
    """إضافة مقتطف جديد."""
    indexer = SnipIndexer()
    
    # إذا كان الإدخال من أنبوب (pipe)
    if not sys.stdin.isatty():
        code = sys.stdin.read().strip()
    elif args.file:
        with open(args.file, 'r') as f:
            code = f.read()
    else:
        print("❌ يجب توفير كود عبر الأنبوب (|) أو ملف (--file)")
        print("مثال: cat script.py | snipkeep add --desc 'سكربت تنظيف'")
        sys.exit(1)
    
    if not code:
        print("❌ لم يتم توفير أي كود.")
        sys.exit(1)
    
    result = indexer.add(
        code=code,
        description=args.desc or "",
        tags=args.tags or "",
        source="file" if args.file else "pipe",
        file_path=args.file or "",
    )
    
    print(f"✅ تم حفظ المقتطف!")
    print(f"   المعرف: {result['id']}")
    print(f"   اللغة: {result['language']}")
    print(f"   الوسوم: {result['tags'] or 'لا يوجد'}")

def cmd_list(args):
    """عرض كل المقتطفات."""
    from rich.table import Table
    from rich.console import Console
    
    indexer = SnipIndexer()
    snippets = indexer.list_all()
    
    if not snippets:
        print("📭 المكتبة فارغة. أضف مقتطفك الأول:")
        print("   cat script.py | snipkeep add --desc 'وصف المقتطف'")
        return
    
    console = Console()
    table = Table(title="📚 مكتبة المقتطفات", show_lines=False)
    table.add_column("ID", style="cyan", width=8)
    table.add_column("الوصف", style="white")
    table.add_column("اللغة", style="green", width=10)
    table.add_column("الوسوم", style="yellow", width=20)
    table.add_column("مرات التشغيل", style="magenta", width=10)
    
    for snip in snippets:
        desc = snip['description'] or "(بدون وصف)"
        if len(desc) > 50:
            desc = desc[:47] + "..."
        
        table.add_row(
            snip['id'],
            desc,
            snip['language'] or "?",
            snip['tags'] or "-",
            str(snip['run_count']),
        )
    
    console.print(table)

def cmd_search(args):
    """البحث بالمعنى."""
    from rich.table import Table
    from rich.console import Console
    from rich.panel import Panel
    
    query = ' '.join(args.query)
    
    try:
        engine = SearchEngine()
        results = engine.search(query, top_k=args.top)
    except Exception as e:
        print(f"⚠️ خطأ في محرك البحث: {e}")
        print("🔍 استخدام البحث النصي كبديل...")
        engine = SearchEngine()
        results = engine.quick_search(query)[:args.top]
    
    if not results:
        print(f"🔍 لا توجد نتائج لـ: '{query}'")
        print("💡 جرب وصفاً مختلفاً أو أضف مقتطفات جديدة.")
        return
    
    console = Console()
    
    for i, (score, snip) in enumerate(results, 1):
        similarity_pct = int(score * 100)
        
        # عرض المقتطف مع تمييز اللغة
        from pygments import highlight
        from pygments.lexers import get_lexer_by_name
        from pygments.formatters import TerminalFormatter
        
        try:
            lexer = get_lexer_by_name(snip['language'] or 'text', stripall=True)
        except:
            lexer = get_lexer_by_name('text', stripall=True)
        
        colored_code = highlight(snip['code'][:500], lexer, TerminalFormatter())
        
        panel = Panel(
            colored_code,
            title=f"[bold cyan]#{i} [ID: {snip['id']}] | {snip['language']} | تطابق: {similarity_pct}%[/]",
            subtitle=f"[yellow]{snip['tags'] or 'بدون وسوم'}[/] | {snip['description'] or 'بدون وصف'}",
            border_style="blue",
        )
        console.print(panel)
        print()

def cmd_show(args):
    """عرض مقتطف محدد."""
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import TerminalFormatter
    
    indexer = SnipIndexer()
    snip = indexer.get(args.id)
    
    if not snip:
        print(f"❌ لا يوجد مقتطف بالمعرف: {args.id}")
        sys.exit(1)
    
    try:
        lexer = get_lexer_by_name(snip['language'] or 'text', stripall=True)
    except:
        lexer = get_lexer_by_name('text', stripall=True)
    
    print(f"\n{'='*60}")
    print(f"📋 المعرف: {snip['id']}")
    print(f"📝 الوصف: {snip['description'] or 'لا يوجد'}")
    print(f"🔤 اللغة: {snip['language']}")
    print(f"🏷️  الوسوم: {snip['tags'] or 'لا يوجد'}")
    print(f"📅 تاريخ الإنشاء: {snip['created_at'][:10]}")
    print(f"▶️  مرات التشغيل: {snip['run_count']}")
    print(f"{'='*60}\n")
    
    print(highlight(snip['code'], lexer, TerminalFormatter()))
    print()
    
    if args.copy:
        copy_to_clipboard(snip['code'])
        print("📋 تم نسخ الكود إلى الحافظة.")

def cmd_run(args):
    """تشغيل مقتطف في بيئة آمنة."""
    from rich.console import Console
    from rich.panel import Panel
    
    indexer = SnipIndexer()
    snip = indexer.get(args.id)
    
    if not snip:
        print(f"❌ لا يوجد مقتطف بالمعرف: {args.id}")
        sys.exit(1)
    
    print(f"\n🚀 تشغيل المقتطف [{snip['id']}] ({snip['language']})...")
    print("-" * 40)
    
    sandbox = Sandbox()
    result = sandbox.run(snip['code'], snip['language'])
    
    console = Console()
    
    if result['stdout']:
        console.print(Panel(result['stdout'], title="📤 المخرجات", border_style="green"))
    
    if result['stderr']:
        console.print(Panel(result['stderr'], title="⚠️ الأخطاء", border_style="red"))
    
    if result['success']:
        print(f"✅ تم التنفيذ بنجاح (كود الخروج: {result['exit_code']})")
    else:
        print(f"❌ فشل التنفيذ (كود الخروج: {result['exit_code']})")
    
    # تحديث عداد التشغيل
    indexer.db.increment_run_count(args.id)

def cmd_delete(args):
    """حذف مقتطف."""
    indexer = SnipIndexer()
    snip = indexer.get(args.id)
    
    if not snip:
        print(f"❌ لا يوجد مقتطف بالمعرف: {args.id}")
        sys.exit(1)
    
    confirm = input(f"⚠️  هل أنت متأكد من حذف المقتطف '{snip['description'] or snip['id']}'؟ (y/N): ")
    if confirm.lower() == 'y':
        indexer.delete(args.id)
        print("🗑️  تم الحذف.")
    else:
        print("❌ تم الإلغاء.")

def cmd_edit(args):
    """تعديل وصف مقتطف."""
    indexer = SnipIndexer()
    snip = indexer.get(args.id)
    
    if not snip:
        print(f"❌ لا يوجد مقتطف بالمعرف: {args.id}")
        sys.exit(1)
    
    indexer.update_description(args.id, args.desc)
    print(f"✅ تم تحديث وصف المقتطف [{args.id}].")

def main():
    parser = argparse.ArgumentParser(
        description="🧠 SnipKeep - بنك المقتطفات الذكي بالمعنى",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  # إضافة مقتطف
  cat script.py | snipkeep add --desc "فرز قائمة قواميس"
  
  # بحث بالمعنى
  snipkeep search "كيف أرتب قائمة معقدة"
  
  # عرض مقتطف
  snipkeep show abc123
  
  # تشغيل مقتطف في بيئة آمنة
  snipkeep run abc123
  
  # عرض المكتبة
  snipkeep list
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='الأوامر المتاحة')
    
    # أمر add
    parser_add = subparsers.add_parser('add', help='إضافة مقتطف جديد')
    parser_add.add_argument('--desc', '-d', help='وصف المقتطف')
    parser_add.add_argument('--tags', '-t', help='وسوم مفصولة بفواصل')
    parser_add.add_argument('--file', '-f', help='قراءة من ملف بدلاً من الأنبوب')
    
    # أمر list
    parser_list = subparsers.add_parser('list', help='عرض كل المقتطفات')
    
    # أمر search
    parser_search = subparsers.add_parser('search', help='بحث بالمعنى')
    parser_search.add_argument('query', nargs='+', help='عبارة البحث')
    parser_search.add_argument('--top', '-n', type=int, default=5, help='عدد النتائج')
    
    # أمر show
    parser_show = subparsers.add_parser('show', help='عرض مقتطف محدد')
    parser_show.add_argument('id', help='معرف المقتطف')
    parser_show.add_argument('--copy', '-c', action='store_true', help='نسخ للحافظة')
    
    # أمر run
    parser_run = subparsers.add_parser('run', help='تشغيل مقتطف في بيئة آمنة')
    parser_run.add_argument('id', help='معرف المقتطف')
    
    # أمر delete
    parser_delete = subparsers.add_parser('delete', help='حذف مقتطف')
    parser_delete.add_argument('id', help='معرف المقتطف')
    
    # أمر edit
    parser_edit = subparsers.add_parser('edit', help='تعديل وصف مقتطف')
    parser_edit.add_argument('id', help='معرف المقتطف')
    parser_edit.add_argument('--desc', '-d', required=True, help='الوصف الجديد')
    
    args = parser.parse_args()
    
    if not args.command:
        print_banner()
        parser.print_help()
        sys.exit(0)
    
    # توجيه الأمر
    commands = {
        'add': cmd_add,
        'list': cmd_list,
        'search': cmd_search,
        'show': cmd_show,
        'run': cmd_run,
        'delete': cmd_delete,
        'edit': cmd_edit,
    }
    
    commands[args.command](args)

if __name__ == '__main__':
    main()
