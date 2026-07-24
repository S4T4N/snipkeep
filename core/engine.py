# core/engine.py
import numpy as np
from sentence_transformers import SentenceTransformer
from core.db import SnipDB

class SearchEngine:
    def __init__(self):
        print("🔄 تحميل نموذج الذكاء الاصطناعي (يحدث مرة واحدة فقط)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db = SnipDB()
        print("✅ النموذج جاهز.")
        self._index_all()

    def _index_all(self):
        """يفهرس كل المقتطفات التي ليس لها تضمين بعد."""
        all_snips = self.db.get_all_snippets()
        need_index = [s for s in all_snips if s.get('embedding') is None]
        
        if need_index:
            print(f"📊 فهرسة {len(need_index)} مقتطف جديد...")
            for snip in need_index:
                text_to_embed = f"{snip['description']} {snip['tags']} {snip['code'][:500]}"
                embedding = self.model.encode(text_to_embed).tobytes()
                self.db.update_embedding(snip['id'], embedding)
            print("✅ الفهرسة اكتملت.")

    def search(self, query, top_k=5):
        """يبحث بالمعنى ويرجع أفضل النتائج."""
        query_embedding = self.model.encode(query)
        results = []
        
        for snip in self.db.get_all_snippets():
            if snip.get('embedding') is not None:
                db_embedding = np.frombuffer(snip['embedding'])
                similarity = float(np.dot(query_embedding, db_embedding))
                results.append((similarity, snip))
        
        results.sort(key=lambda x: x[0], reverse=True)
        
        # فلترة النتائج الضعيفة جداً
        filtered = [(sim, snip) for sim, snip in results if sim > 0.2]
        
        return filtered[:top_k]

    def quick_search(self, query):
        """بحث نصي سريع كاحتياطي."""
        return [(1.0, s) for s in self.db.search_by_text(query)]
