from sqladmin import ModelView
from wtforms import TextAreaField
from wtforms.widgets import TextArea

from app.models import (
    User, Region, Category, Contractor, ContractorPhoto, Review
)


class UserAdmin(ModelView, model=User):
    """Админка пользователей"""
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"
    
    column_list = [
        User.id,
        User.telegram_id,
        User.username,
        User.first_name,
        User.is_blocked,
        User.is_approved,
        User.is_admin,
        User.invite_token,
        User.preferred_region,
        User.created_at,
        User.last_activity
    ]
    
    column_searchable_list = [User.username, User.first_name, User.last_name, User.telegram_id]
    column_sortable_list = [User.id, User.telegram_id, User.created_at, User.last_activity]
    column_default_sort = [(User.last_activity, True)]
    
    form_columns = [
        User.telegram_id,
        User.username,
        User.first_name,
        User.last_name,
        User.is_blocked,
        User.is_approved,
        User.is_admin,
        User.preferred_region
    ]
    
    can_create = False
    can_delete = False
    
    column_labels = {
        User.is_blocked: "Заблокирован",
        User.is_approved: "Одобрен",
        User.is_admin: "Администратор",
        User.invite_token: "Токен"
    }


class RegionAdmin(ModelView, model=Region):
    """Админка регионов"""
    name = "Регион"
    name_plural = "Регионы"
    icon = "fa-solid fa-location-dot"
    
    column_list = [Region.id, Region.name, Region.region, Region.is_active, Region.created_at]
    column_searchable_list = [Region.name, Region.region]
    column_sortable_list = [Region.id, Region.name, Region.created_at]
    column_default_sort = [(Region.name, False)]
    
    form_columns = [Region.name, Region.region, Region.is_active]


class CategoryAdmin(ModelView, model=Category):
    """Админка категорий"""
    name = "Категория"
    name_plural = "Категории"
    icon = "fa-solid fa-folder"
    
    column_list = [
        Category.id,
        Category.name,
        Category.parent,
        Category.icon,
        Category.order_index,
        Category.created_at
    ]
    
    column_searchable_list = [Category.name]
    column_sortable_list = [Category.id, Category.name, Category.order_index, Category.created_at]
    column_default_sort = [(Category.order_index, False), (Category.name, False)]
    
    form_columns = [
        Category.name,
        Category.description,
        Category.parent,
        Category.icon,
        Category.order_index
    ]
    
    form_args = {
        "description": {
            "widget": TextArea()
        }
    }


class ContractorAdmin(ModelView, model=Contractor):
    """Админка исполнителей"""
    name = "Исполнитель"
    name_plural = "Исполнители"
    icon = "fa-solid fa-briefcase"
    
    column_list = [
        Contractor.id,
        Contractor.name,
        Contractor.region,
        Contractor.phone,
        Contractor.rating,
        Contractor.reviews_count,
        Contractor.views_count,
        Contractor.is_active,
        Contractor.is_premium,
        Contractor.created_at
    ]
    
    column_searchable_list = [Contractor.name, Contractor.phone, Contractor.description]
    column_sortable_list = [
        Contractor.id,
        Contractor.name,
        Contractor.rating,
        Contractor.reviews_count,
        Contractor.views_count,
        Contractor.created_at
    ]
    column_default_sort = [(Contractor.created_at, True)]
    
    form_columns = [
        Contractor.name,
        Contractor.description,
        Contractor.phone,
        Contractor.additional_phones,
        Contractor.telegram_username,
        Contractor.address,
        Contractor.region,
        Contractor.latitude,
        Contractor.longitude,
        Contractor.categories,
        Contractor.is_active,
        Contractor.is_premium,
        Contractor.premium_until
    ]
    
    form_args = {
        "description": {
            "widget": TextArea()
        }
    }
    
    column_formatters = {
        Contractor.rating: lambda m, a: f"{float(m.rating):.2f}" if m.rating else "0.00",
    }


class ContractorPhotoAdmin(ModelView, model=ContractorPhoto):
    """Админка фотографий исполнителей"""
    name = "Фотография"
    name_plural = "Фотографии"
    icon = "fa-solid fa-image"
    
    column_list = [
        ContractorPhoto.id,
        ContractorPhoto.contractor,
        ContractorPhoto.is_main,
        ContractorPhoto.order_index,
        ContractorPhoto.uploaded_at
    ]
    
    column_sortable_list = [
        ContractorPhoto.id,
        ContractorPhoto.order_index,
        ContractorPhoto.uploaded_at
    ]
    column_default_sort = [(ContractorPhoto.uploaded_at, True)]
    
    form_columns = [
        ContractorPhoto.contractor,
        ContractorPhoto.file_id,
        ContractorPhoto.file_path,
        ContractorPhoto.is_main,
        ContractorPhoto.order_index
    ]


class ReviewAdmin(ModelView, model=Review):
    """Админка отзывов"""
    name = "Отзыв"
    name_plural = "Отзывы"
    icon = "fa-solid fa-star"
    
    column_list = [
        Review.id,
        Review.contractor,
        Review.user_name,
        Review.rating,
        Review.comment,
        Review.is_moderated,
        Review.is_visible,
        Review.created_at
    ]
    
    column_searchable_list = [Review.user_name, Review.comment]
    column_sortable_list = [
        Review.id,
        Review.rating,
        Review.created_at
    ]
    column_default_sort = [(Review.created_at, True)]
    
    form_columns = [
        Review.contractor,
        Review.user,
        Review.user_name,
        Review.rating,
        Review.comment,
        Review.is_moderated,
        Review.is_visible
    ]
    
    form_args = {
        "comment": {
            "widget": TextArea()
        }
    }
    
    column_formatters = {
        Review.rating: lambda m, a: "⭐" * m.rating if m.rating else "",
        Review.comment: lambda m, a: (m.comment[:50] + "...") if m.comment and len(m.comment) > 50 else m.comment or "",
    }

