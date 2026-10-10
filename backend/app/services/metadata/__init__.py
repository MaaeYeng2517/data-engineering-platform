"""Metadata management system"""
from typing import Any, Dict, List, Optional
import logging
from backend.app.utils.time import utcnow

logger = logging.getLogger(__name__)


class MetadataEngine:
    """Manage metadata schemas, taxonomies, and validation"""
    
    def __init__(self):
        self.schemas: Dict[str, Dict] = {}
        self.taxonomies: Dict[str, Dict] = {}
        self.ontologies: Dict[str, Dict] = {}
    
    def register_schema(self, schema_id: str, schema: Dict[str, Any]):
        """Register a metadata schema"""
        self.schemas[schema_id] = schema
        logger.info(f"Registered schema: {schema_id}")
    
    def get_schema(self, schema_id: str) -> Optional[Dict]:
        """Get schema by ID"""
        return self.schemas.get(schema_id)
    
    def validate(self, schema_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against a registered schema"""
        schema = self.schemas.get(schema_id)
        if not schema:
            return {"valid": False, "error": "Schema not found"}
        return self.validate_fields(schema.get("fields", []), data)

    @staticmethod
    def validate_fields(fields: List[Dict[str, Any]], data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against a field definition list.

        Split out from `validate` so a schema loaded from Postgres can be
        checked without being registered in this process.
        """
        errors = []
        for field in fields:
            field_name = field.get("name")
            if not field_name:
                continue

            if field.get("required", False) and field_name not in data:
                errors.append(f"Missing required field: {field_name}")

            if field_name in data:
                value = data[field_name]
                field_type = field.get("type", "string")

                # Type validation
                if field_type == "integer" and not isinstance(value, int):
                    errors.append(f"Field {field_name} must be integer")
                elif field_type == "string" and not isinstance(value, str):
                    errors.append(f"Field {field_name} must be string")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "validated_at": utcnow().isoformat(),
        }
    
    def add_tags(self, data: Dict[str, Any], tags: List[str]) -> Dict[str, Any]:
        """Add tags to metadata"""
        existing_tags = data.get("tags", [])
        data["tags"] = list(set(existing_tags + tags))
        return data
    
    def classify(self, data: Dict[str, Any], taxonomy_id: str) -> Dict[str, Any]:
        """Classify data using taxonomy"""
        taxonomy = self.taxonomies.get(taxonomy_id)
        if not taxonomy:
            return data
        
        # Simple classification based on keywords
        content = str(data.get("content", "")).lower()
        for category, keywords in taxonomy.items():
            for keyword in keywords:
                if keyword.lower() in content:
                    data["category"] = category
                    data["classification_confidence"] = 0.8
                    break
        
        return data
    
    def register_taxonomy(self, taxonomy_id: str, taxonomy: Dict[str, Any]):
        """Register a taxonomy"""
        self.taxonomies[taxonomy_id] = taxonomy
    
    def get_taxonomy(self, taxonomy_id: str) -> Optional[Dict]:
        """Get taxonomy by ID"""
        return self.taxonomies.get(taxonomy_id)


# Global metadata engine
metadata_engine = MetadataEngine()

# Register default taxonomy
metadata_engine.register_taxonomy("domain", {
    "Education": ["education", "course", "student", "teacher", "school"],
    "Computer Science": ["computer", "programming", "software", "algorithm", "database"],
    "Database": ["database", "sql", "dbms", "table", "query"],
    "AI/ML": ["ai", "machine learning", "neural network", "model", "training"]
})