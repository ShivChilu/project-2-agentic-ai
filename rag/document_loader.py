"""Policy Document Loader for Local RAG."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import re


@dataclass
class PolicyDocument:
    document_id: str
    title: str
    category: str
    clause: str
    description: str
    content: str


def load_policy_documents(policy_dir: Optional[str] = None) -> List[PolicyDocument]:
    """Load and parse markdown policy documents from policy_dir."""
    if policy_dir is None:
        policy_dir = str(Path(__file__).resolve().parent.parent / "data" / "policies")
        
    p_dir = Path(policy_dir)
    if not p_dir.exists():
        raise FileNotFoundError(f"Policy directory not found: {policy_dir}")
        
    documents: List[PolicyDocument] = []
    
    for file_path in sorted(p_dir.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")
        
        doc_id_match = re.search(r"\*\*Document ID:\*\*\s*([^\n\r]+)", text)
        title_match = re.search(r"\*\*Document Title:\*\*\s*([^\n\r]+)", text)
        cat_match = re.search(r"\*\*Category:\*\*\s*([^\n\r]+)", text)
        clause_match = re.search(r"\*\*Policy Clause:\*\*\s*([^\n\r]+)", text)
        desc_match = re.search(r"\*\*Description:\*\*\s*([^\n\r]+)", text)
        
        doc_id = doc_id_match.group(1).strip() if doc_id_match else file_path.stem.upper()
        title = title_match.group(1).strip() if title_match else file_path.stem.replace("_", " ").title()
        category = cat_match.group(1).strip() if cat_match else "General"
        clause = clause_match.group(1).strip() if clause_match else f"CLAUSE-{doc_id}"
        description = desc_match.group(1).strip() if desc_match else text.strip()
        
        # Combine fields into an indexed text chunk for TF-IDF
        full_text = f"{title}. Category: {category}. Clause: {clause}. {description} {text}"
        
        documents.append(PolicyDocument(
            document_id=doc_id,
            title=title,
            category=category,
            clause=clause,
            description=description,
            content=full_text
        ))
        
    return documents
