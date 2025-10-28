from django.shortcuts import render
from elasticsearch_dsl.query import MultiMatch
from .documents import ProductDocument
from django.db.models import Case, When
from .models import Product


# Create your views here.
def index(request):
    q = request.GET.get("q")
    context = {}
    if q:
        query = MultiMatch(query=q, fields=["name", "main_category", "sub_category"])
        p = ProductDocument.search().query(query)[0:20]
        elastic_ids = [hit.meta.id for hit in p]
        if elastic_ids:
            products = Product.objects.filter(id__in=elastic_ids)
            preserved_order = Case(*[When(id=id, then=pos) for pos, id in enumerate(elastic_ids)])
            products = products.order_by(preserved_order)
            context["products"] = products
    return render(request, "index.html", context)
