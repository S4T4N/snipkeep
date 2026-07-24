# core/snip_indexer.py
from core.db import SnipDB
from core.classifier import LanguageClassifier

class SnipIndexer:
    def __init__(self):
        self.db = SnipDB()
        self.classifier = LanguageClassifier()

    def add(self, code, description="", tags="", source="manual", file_path=""):
        """يضيف مقتطفاً جديداً مع تصنيف تلقائي."""
        # كشف اللغة تلقائياً إن لم تحدد
        language = self.classifier.classify(code)
        
        # استخراج وسوم من التعليقات
        extracted_tags = self.classifier.extract_tags(code)
        
        # دمج الوسوم المدخلة مع المستخرجة
        all_tags = set()
        if tags:
            for t in tags.split(","):
                all_tags.add(t.strip().lower())
        for t in extracted_tags:
            all_tags.add(t)
        
        tags_str = ",".join(sorted(all_tags))
        
        # حفظ في القاعدة
        snip_id = self.db.add_snippet(
            code=code,
            language=language,
            description=description,
            tags=tags_str,
            source=source,
            file_path=file_path
        )
        
        return {
            "id": snip_id,
            "language": language,
            "tags": tags_str,
        }

    def list_all(self):
        """يرجع كل المقتطفات."""
        return self.db.get_all_snippets()

    def get(self, snip_id):
        """يرجع مقتطفاً واحداً."""
        return self.db.get_snippet_by_id(snip_id)

    def update_description(self, snip_id, description):
        """يحدث وصف مقتطف."""
        self.db.update_description(snip_id, description)

    def delete(self, snip_id):
        """يحذف مقتطفاً."""
        self.db.delete_snippet(snip_id)
