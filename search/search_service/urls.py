from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    path("api/track-action/", views.track_action),
    # path("image_search/", views.search_image),
    # path("api/search_by_image/", views.search_similar_images)
    path('api/search/', views.search_products, name='search_products'),
    path('api/search_by_image/', views.search_by_image, name='search_by_image'),
]
