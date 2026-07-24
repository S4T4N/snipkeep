# core/classifier.py
import re

class LanguageClassifier:
    """يكتشف لغة البرمجة من الكود تلقائياً."""
    
    PATTERNS = {
        "python": [
            r"^import\s+\w+", r"^from\s+\w+\s+import", r"def\s+\w+\s*\(",
            r"class\s+\w+.*:", r"^\s*@\w+", r"print\s*\(", r"if __name__",
        ],
        "bash": [
            r"^#!/bin/bash", r"^#!/usr/bin/env bash", r"\$\{?\w+\}?",
            r"^if\s+\[\[", r"^esac", r"^fi", r"^done",
        ],
        "javascript": [
            r"console\.log", r"const\s+\w+\s*=", r"let\s+\w+\s*=",
            r"function\s+\w+\s*\(", r"=>\s*\{", r"require\s*\(",
        ],
        "sql": [
            r"SELECT\s+.+\s+FROM", r"CREATE\s+TABLE", r"INSERT\s+INTO",
            r"ALTER\s+TABLE", r"DROP\s+TABLE",
        ],
    }

    @classmethod
    def classify(cls, code):
        """يحدد اللغة الأنسب للكود المعطى."""
        scores = {}
        code_lower = code.lower()
        code_normal = code
        
        for lang, patterns in cls.PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, code_normal, re.MULTILINE | re.IGNORECASE)
                score += len(matches)
            if score > 0:
                scores[lang] = score
        
        if not scores:
            return "text"
        
        return max(scores, key=scores.get)

    @classmethod
    def extract_tags(cls, code):
        """يستخرج وسوماً من التعليقات داخل الكود."""
        tags = set()
        # تعليقات بايثون (# TODO: ...) أو (# tag: شبكات, أمان)
        comment_tags = re.findall(r'#\s*(?:tag|وسم|keyword)s?:\s*([^\n]+)', code, re.IGNORECASE)
        for tag_line in comment_tags:
            for tag in re.split(r'[,\s]+', tag_line):
                if tag.strip():
                    tags.add(tag.strip().lower())
        return list(tags)
