from django.http import JsonResponse
from django.shortcuts import render
from elasticsearch_dsl.query import MultiMatch
from .documents import ProductDocument
from django.db.models import Case, When
from .models import Product
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
from elasticsearch_dsl import Search
import base64
from django.http import JsonResponse
import json
import io
from .model_manager import clip_manager
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def index(request):
    q = request.GET.get("q")
    context = {}
    if request.method == "GET" and q:
        query = MultiMatch(query=q, fields=["name", "main_category", "sub_category"])
        p = ProductDocument.search().query(query)[0:20]
        elastic_ids = [hit.meta.id for hit in p]
        if elastic_ids:
            products = Product.objects.filter(id__in=elastic_ids)
            preserved_order = Case(*[When(id=id, then=pos) for pos, id in enumerate(elastic_ids)])
            products = products.order_by(preserved_order)
            context["products"] = products
    if request.method == "POST":
        try:
            image_file = request.FILES.get('image')
            if image_file:
                # Открываем изображение напрямую из файла
                image = Image.open(image_file).convert("RGB")

                # Загружаем модель CLIP
                query_embedding = clip_manager.get_embedding(image)

                # Поиск в Elasticsearch
                s = Search(index="image_emb")

                # Запрос для векторного поиска
                search_query = {
                    "query": {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                "params": {"query_vector": query_embedding}
                            }
                        }
                    }
                }

                # Выполняем поиск
                response = s.update_from_dict(search_query).extra(size=20).execute()

                # Формируем результаты
                results = []
                for hit in response:
                    results.append({
                        "image": "/static/" + hit.image_path.replace("\\", "/")
                    })
                context["products"] = results

        except Exception as e:
            print(e)
            context["error"] = f"Ошибка при поиске: {str(e)}"
        print(context)
    return render(request, "index.html", context)


@require_http_methods(["GET"])
def search_products(request):
    query = request.GET.get('q', '')

    # Проверяем AJAX запрос
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        # Ваша логика поиска
        query = MultiMatch(query=query, fields=["name", "main_category", "sub_category"])
        p = ProductDocument.search().query(query)[0:20]
        elastic_ids = [hit.meta.id for hit in p]
        if elastic_ids:
            products = Product.objects.filter(id__in=elastic_ids)
            preserved_order = Case(*[When(id=id, then=pos) for pos, id in enumerate(elastic_ids)])
            products = products.order_by(preserved_order)
        else:
            products = []

        # Подготавливаем данные для JSON
        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'image': product.image,
                'main_category': product.main_category,
                'sub_category': product.sub_category,
                'discount_price': str(product.discount_price) if product.discount_price else None,
                'actual_price': str(product.actual_price) if product.actual_price else None,
            })

        return JsonResponse({
            'products': products_data,
            'count': len(products_data)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def search_by_image(request):
    # Проверяем AJAX запрос
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        image_file = request.FILES.get('image')

        if not image_file:
            return JsonResponse({'error': 'No image provided'}, status=400)

        # Логика поиска по изображению
        image = Image.open(image_file).convert("RGB")

        query_embedding = clip_manager.get_embedding(image)

        # Поиск в Elasticsearch
        s = Search(index="image_emb")

        # Запрос для векторного поиска
        search_query = {
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": query_embedding}
                    }
                }
            }
        }

        # Выполняем поиск
        response = s.update_from_dict(search_query).extra(size=20).execute()

        # Формируем результаты
        products_data = []
        for hit in response:
            products_data.append({
                "image": "/static/" + hit.image_path.replace("\\", "/")
            })


        return JsonResponse({
            'products': products_data,
            'count': len(products_data)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def track_action(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')
        try:
            print(action, product_id)
            return JsonResponse({'status': 'success'})
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found'})

    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'})