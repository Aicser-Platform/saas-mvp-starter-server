from sqlalchemy.orm import Session
from uuid import UUID
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_categories(db: Session, skip: int = 0, limit: int = 200):
    return db.query(Category).order_by(Category.name).offset(skip).limit(limit).all()


def get_category(db: Session, category_id: UUID):
    return db.query(Category).filter(Category.id == category_id).first()


def create_category(db: Session, category: CategoryCreate):
    db_category = Category(
        name=category.name,
        description=category.description,
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category_id: UUID, updates: CategoryUpdate):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        return None
    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: UUID):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        return None
    db.delete(db_category)
    db.commit()
    return db_category
