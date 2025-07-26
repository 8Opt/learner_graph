from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from app.core.database import Base
from app.core.exceptions import NotFoundException

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository class with common CRUD operations."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        obj = self.model(**obj_in)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get a record by ID."""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_or_404(self, db: Session, id: int) -> ModelType:
        """Get a record by ID or raise 404."""
        obj = self.get(db, id)
        if obj is None:
            raise NotFoundException(f"{self.model.__name__} with id {id} not found")
        return obj

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
    ) -> List[ModelType]:
        """Get multiple records with optional filtering and pagination."""
        query = db.query(self.model)

        # Apply filters
        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    else:
                        filter_conditions.append(getattr(self.model, key) == value)
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            query = query.order_by(
                desc(order_column) if order_desc else asc(order_column)
            )

        return query.offset(skip).limit(limit).all()

    def count(self, db: Session, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        query = db.query(self.model)

        if filters:
            filter_conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        filter_conditions.append(getattr(self.model, key).in_(value))
                    else:
                        filter_conditions.append(getattr(self.model, key) == value)
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))

        return query.count()

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Dict[str, Any]
    ) -> ModelType:
        """Update a record."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> ModelType:
        """Delete a record."""
        obj = db.query(self.model).get(id)
        if obj is None:
            raise NotFoundException(f"{self.model.__name__} with id {id} not found")

        db.delete(obj)
        db.commit()
        return obj

    def soft_delete(self, db: Session, *, id: int) -> ModelType:
        """Soft delete a record (if model supports it)."""
        obj = self.get_or_404(db, id)

        if hasattr(obj, "is_deleted"):
            obj.is_deleted = True
            if hasattr(obj, "deleted_at"):
                from datetime import datetime

                obj.deleted_at = datetime.utcnow()

            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj
        else:
            # Fallback to hard delete if soft delete not supported
            return self.delete(db, id=id)

    def bulk_create(
        self, db: Session, *, objs_in: List[Dict[str, Any]]
    ) -> List[ModelType]:
        """Create multiple records in bulk."""
        objs = [self.model(**obj_data) for obj_data in objs_in]
        db.add_all(objs)
        db.commit()
        for obj in objs:
            db.refresh(obj)
        return objs

    def exists(self, db: Session, *, filters: Dict[str, Any]) -> bool:
        """Check if a record exists with given filters."""
        return self.count(db, filters=filters) > 0
