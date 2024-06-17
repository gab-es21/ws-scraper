from rest_framework.views import APIView
from rest_framework.response import Response
from firebase_admin import firestore

db = firestore.client()

class ProductList(APIView):
    def get(self, request):
        products = db.collection('products').stream()
        product_list = [{doc.id: doc.to_dict()} for doc in products]
        return Response(product_list)

class ProductDetail(APIView):
    def get(self, request, product_id):
        product = db.collection('products').document(product_id).get()
        if product.exists:
            return Response(product.to_dict())
        return Response(status=404)

class ProductFlavorHistory(APIView):
    def get(self, request, product_id, flavor_id):
        history = db.collection('products').document(product_id).collection('flavors').document(flavor_id).collection('history').stream()
        history_list = [{doc.id: doc.to_dict()} for doc in history]
        return Response(history_list)