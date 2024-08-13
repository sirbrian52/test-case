import re
from rest_framework import viewsets,status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter,OpenApiResponse,OpenApiExample
from .models import Customer,Product,SaleItem,Sale
from .serializer import CustomerSerializer,ProductSerializer,SaleSerializer,SaleItemSerializer
from rest_framework.decorators import action
from django.utils.dateparse import parse_datetime
from django.db.models import Q,F,Sum
from django.db.models.functions import TruncDate, TruncHour, TruncMinute
from django.utils.timezone import make_aware
from datetime import datetime , timedelta
from django.db import transaction


@extend_schema(tags = ['customer'])
class CustomerViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing, creating, retrieving customers, and searching by name.
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_queryset(self):
        queryset = Customer.objects.all()
        return queryset.order_by('-id')

    @extend_schema(
        request=CustomerSerializer,
        responses={201: CustomerSerializer, 400: OpenApiParameter},
    )
    def create(self, request):
        """
        Create a new customer.
        """
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


    def list(self, request):
        """
        List all customers
        """
        queryset = self.get_queryset()
        customer_name = request.query_params.get('customer_name', None)
        if customer_name is not None:
            queryset = queryset.filter(customer_name__icontains=customer_name)
        serializer = CustomerSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Retrieve a single customer by ID.
        """
        queryset = self.get_queryset()
        customer = queryset.filter(pk=pk).first()
        if customer is None:
            return Response({'detail': 'Not found.'}, status=404)
        serializer = CustomerSerializer(customer)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='ids', description='Comma-separated list of customer IDs',
                required=False, type=str, location=OpenApiParameter.QUERY
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def by_ids(self, request):
        """
        Retrieve customers by a list of IDs.
        """
        ids = request.query_params.get('ids', None)
        if ids:
            ids_list = ids.split(',')
            queryset = self.get_queryset().filter(id__in=ids_list)
            serializer = CustomerSerializer(queryset, many=True)
            return Response(serializer.data)
        return Response({'detail': 'No IDs provided.'}, status=400)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='customer_name', description='Retrieve customers by name',
                required=True, type=str, location=OpenApiParameter.QUERY
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def get_by_name(self, request):
        """
        Retrieve customers by their name.
        """
        customer_name = request.query_params.get('customer_name', None)

        if customer_name:
        # Check for invalid characters (e.g., symbols)
            if not re.match(r'^[a-zA-Z0-9\s]+$', customer_name):
                return Response({'error': 'Invalid input: customer_name contains invalid characters.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if customer_name:
            queryset = self.get_queryset().filter(customer_name__icontains=customer_name)
            serializer = CustomerSerializer(queryset, many=True)
            return Response(serializer.data)
        return Response({'detail': 'No customer_name provided.'}, status=400)   
        

    
@extend_schema(tags = ['product'],)
class ProductViewSet(viewsets.ModelViewSet):
    
    def get_queryset(self):
        return Product.objects.all()
    
    def list(self, request):
        queryset = self.get_queryset()
        product_name = request.query_params.get('product_name', None)
        if product_name:
            queryset = queryset.filter(product_name__icontains=product_name)
        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema( 
        parameters=[
            OpenApiParameter(
                name='product_code', description='Retrieve product by product_code',
                required=True, type=str, location=OpenApiParameter.QUERY
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def retrieve_by_code(self, request):
        product_code = request.query_params.get('product_code', None)
        if not product_code:
            return Response({"error": "Product code is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = self.get_queryset().get(product_code=product_code)
            serializer = ProductSerializer(product)
            
            # Prepare the response message based on conditions
            messages = []
            if product.product_status.lower() == "hold":
                if product.product_stock == 0:
                    messages.append("Product is on hold and out of stock.")
                else:
                    messages.append("Product is on hold.")
            elif product.product_status.lower() == "active":
                if product.product_stock == 0:
                    messages.append("Product stock is not ready.")
                else:
                    messages.append("Product stock is ready.")
            
            response_data = serializer.data
            if messages:
                response_data['messages'] = messages

            return Response(response_data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        
@extend_schema(tags = ['insert sale'],)
class SaleViewSet(viewsets.ModelViewSet):
    @extend_schema(
        request=SaleSerializer,
        responses={
            201: SaleSerializer,
            400: 'Bad Request'
        }
    )
    @transaction.atomic  # Ensures all-or-nothing behavior
    def create(self, request):
        serializer = SaleSerializer(data=request.data)
        if serializer.is_valid():
            sale_items_data = request.data.get('items', [])
            transaction_code = request.data.get('transaction_code', 'N/A')
            customer_id = request.data.get('customer')

            # Fetch the Customer instance
            try:
                customer_instance = Customer.objects.get(pk=customer_id)
            except Customer.DoesNotExist:
                return Response({'error': 'Customer not found'}, status=status.HTTP_400_BAD_REQUEST)

            # Create Sale instance
            sale = Sale.objects.create(
                customer=customer_instance,
                sale_date=request.data.get('sale_date'),
                transaction_code=transaction_code,
            )

            response_data = {
                'customer_id': sale.customer.id if sale.customer else None,
                'transaction_code': sale.transaction_code,
                'transaction_date': sale.sale_date,
                'items': []
            }

            total_item_qty = 0  
            errors = []

            for item_data in sale_items_data:
                product_id = item_data.get('id')
                quantity = item_data.get('qty')

                try:
                    product_instance = Product.objects.get(pk=product_id)
                except Product.DoesNotExist:
                    errors.append({
                        'id': product_id,
                        'error': 'Product not found'
                    })
                    continue

                if quantity > product_instance.product_stock:
                    response_data['items'].append({
                        'id': product_id,
                        'price': item_data.get('price'),
                        'qty': quantity,
                        'status': 'Failed',
                        'message': 'Insufficient stock'
                    })
                    continue

                SaleItem.objects.create(
                    sale=sale,
                    product=product_instance,
                    product_price=item_data.get('price'),
                    item_qty=quantity,
                    is_verify=1
                )

                product_instance.product_stock -= quantity
                product_instance.save()

                response_data['items'].append({
                    'id': product_id,
                    'price': item_data.get('price'),
                    'qty': quantity,
                    'status': 'Success'
                })

                total_item_qty += quantity

            # If there were any errors, handle them accordingly
            if errors:
                # Rollback the transaction
                transaction.set_rollback(True)
                return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

            # Update sale_items_total with the total quantity of successful items
            sale.sale_items_total = total_item_qty
            sale.save()

            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@extend_schema(tags = ['paging'],)
class PagingViewSet(viewsets.ModelViewSet):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='data_periode_start',
                description='Start date in ISO 8601 format (e.g., 2024-08-01)',
                required=True,
                type=str
            ),
            OpenApiParameter(
                name='data_periode_end',
                description='End date in ISO 8601 format (e.g., 2024-08-07)',
                required=True,
                type=str
            ),
            OpenApiParameter(
                name='total_data_show',
                description='Total number of results to show per page',
                required=True,
                type=int
            ),
            OpenApiParameter(
                name='keyword',
                description='Keyword to search for in transaction code or customer name',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='page',
                description='Page number for pagination',
                required=False,
                type=int
            ),
        ],
        description='Retrieve all transactions within the given date range, filtered by a keyword, with a custom response format.'
    )
    @action(detail=False, methods=['get'], url_path='transactions')
    def get_filtered_transactions(self, request):
        start_date = request.query_params.get('data_periode_start')
        end_date = request.query_params.get('data_periode_end')
        total_show_data = int(request.query_params.get('total_data_show', 10))
        keyword = request.query_params.get('keyword', '')
        page = int(request.query_params.get('page', 1))

        if not start_date or not end_date:
            return Response({"error": "Both data_periode_start and data_periode_end are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            start_date = parse_datetime(start_date)
            end_date = parse_datetime(end_date)
        except ValueError:
            return Response({"error": "Invalid date format."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not start_date or not end_date:
            return Response({"error": "Invalid date format."}, status=status.HTTP_400_BAD_REQUEST)

        # Adjust the end date to include the whole day
        end_date = end_date.replace(hour=23, minute=59, second=59)

        # Filter by date range and keyword
        sales = Sale.objects.filter(
            sale_date__range=(start_date, end_date)
        ).filter(
            Q(transaction_code__icontains=keyword) | Q(customer__customer_name__icontains=keyword)
        )

        # Pagination logic
        total_data = sales.count()
        total_page = (total_data // total_show_data) + (1 if total_data % total_show_data != 0 else 0)
        start_index = (page - 1) * total_show_data
        end_index = start_index + total_show_data
        paginated_sales = sales[start_index:end_index]
        

        rows = []
        for sale in paginated_sales:
            rows.append({
                "transaction_code": sale.transaction_code,
                "sale_date": sale.sale_date.strftime("%d/%m/%y"),
                "customer": sale.customer.customer_name if sale.customer else "N/A",
                "total_item": sale.sale_items_total,
                "total_price": sum(item.product_price * item.item_qty for item in sale.saleitem_set.all())
            })

        response_data = {
            "params": [
                {
                    "keyword": keyword,
                    "data_periode_start": start_date.strftime("%d/%m/%Y"),
                    "data_periode_end": end_date.strftime("%d/%m/%Y"),
                    "total_data_show": total_show_data
                }
            ],
            "data": [
                {
                    "keyword": keyword,
                    "total_data": total_data,
                    "total_data_show": total_show_data,
                    "total_page": total_page,
                    "Page": page,
                    "status": 200,
                    "rows": rows
                }
            ]
        }

        return Response(response_data, status=status.HTTP_200_OK)

@extend_schema(tags= ['Cart Compare'])
class CartCompareViewSet(viewsets.ModelViewSet):

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='data_periode_start',
                description='Start datetime of the period in ISO 8601 format (e.g., 2024-08-01T00:00:00Z)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='data_periode_end',
                description='End datetime of the period in ISO 8601 format (e.g., 2024-08-07T23:59:59Z)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='keyword',
                description='Keyword for searching by transaction code or customer name',
                required=False,
                type=str
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Comparison of transactions by date and time range',
                examples={
                    'application/json': {
                        "params": [
                            {
                                "keyword": "",
                                "dates": [
                                    {"date": "2024-08-01"},
                                    {"date": "2024-08-02"}
                                ]
                            }
                        ],
                        "data": [
                            {
                                "date:2024-08-01": [
                                    {"time": "01:00", "total": 100},
                                    {"time": "02:00", "total": 150}
                                ],
                                "date:2024-08-02": [
                                    {"time": "01:00", "total": 200},
                                    {"time": "02:00", "total": 250}
                                ]
                            }
                        ]
                    }
                }
            ),
            400: OpenApiResponse(
                description='Error response for invalid parameters',
                examples={
                    'application/json': {
                        "error": "Invalid datetime format."
                    }
                }
            )
        },
        description='Retrieve and compare sales transactions by datetime range and keyword.',
    )
    @action(detail=False, methods=['get'], url_path='compare-transactions')
    def compare_transactions(self, request):
        start_date = request.query_params.get('data_periode_start')
        end_date = request.query_params.get('data_periode_end')
        keyword = request.query_params.get('keyword', '')

        # Filter sales data based on datetime range if provided, otherwise get all data
        if start_date and end_date:
            try:
                start_date = parse_datetime(start_date)
                end_date = parse_datetime(end_date)
            except ValueError:
                return Response({"error": "Invalid datetime format."}, status=status.HTTP_400_BAD_REQUEST)
            
            sales = Sale.objects.filter(sale_date__range=(start_date, end_date))
        else:
            sales = Sale.objects.all()
        
        # Apply keyword filtering
        if keyword:
            sales = sales.filter(Q(transaction_code__icontains=keyword) | Q(customer__customer_name__icontains=keyword))
        
        # Get distinct dates for the filtered sales data
        dates = sorted(sales.values_list('sale_date__date', flat=True).distinct())
        
        # Initialize response data
        response_data = {
            "params": [
                {
                    "keyword": keyword,
                    "dates": [{"date": date.strftime('%Y-%m-%d')} for date in dates]
                }
            ],
            "data": []
        }
        
        # If no dates found, handle case for all data
        if not dates:
            sales = Sale.objects.all()
            dates = sorted(sales.values_list('sale_date__date', flat=True).distinct())
        
        # Process each date
        for date in dates:
            hourly_data = (
                sales.filter(sale_date__date=date)
                .annotate(
                    hour=TruncHour('sale_date'),
                    minute=TruncMinute('sale_date')
                )
                .values('hour', 'minute')
                .annotate(total=Sum(F('saleitem__product_price') * F('saleitem__item_qty')))
                .order_by('hour', 'minute')  # Order by hour and minute in ascending order
            )
            
            response_data['data'].append({
                f"date:{date.strftime('%Y-%m-%d')}": [
                    {"time": f"{data['hour'].hour:02}:{data['minute'].minute:02}", "total": data['total']} for data in hourly_data
                ]
            })
        
        return Response(response_data, status=status.HTTP_200_OK)    

@extend_schema(tags=['Top 5 Popular'],)
class ProductPopulerViewSet(viewsets.ModelViewSet):
    @extend_schema(
        tags=['Top 5 Popular'],
        parameters=[
            OpenApiParameter(name='data_periode_start', type=str, description='Start date in ISO 8601 format (e.g., 2024-08-01)', required=False),
            OpenApiParameter(name='data_periode_end', type=str, description='End date in ISO 8601 format (e.g., 2024-08-07)', required=False),
        ],
        responses={
            200: OpenApiResponse(
                description='List of top products based on total sales price',
                response={
                    'type': 'object',
                    'properties': {
                        'params': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'data_periode_start': {'type': 'string', 'format': 'date'},
                                    'data_periode_end': {'type': 'string', 'format': 'date'},
                                    'total_data_show': {'type': 5}
                                }
                            }
                        },
                        'data': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'Product_id': {'type': 'integer'},
                                    'Product_code': {'type': 'string'},
                                    'product_name': {'type': 'string'},
                                    'total_items': {'type': 'integer'},
                                    'total_price': {'type': 'number', 'format': 'float'}
                                }
                            }
                        }
                    }
                }
            ),
            400: OpenApiResponse(description='Bad Request')
        }
    )
    def list(self, request):
        # Extract query parameters
        start_date = request.query_params.get('data_periode_start')
        end_date = request.query_params.get('data_periode_end')
        limit = int(request.query_params.get('total_data_show', 5))

        # Convert dates to timezone-aware datetime objects
        if start_date and end_date:
            try:
                start_date = make_aware(datetime.fromisoformat(start_date))
                end_date = make_aware(datetime.fromisoformat(end_date)) + timedelta(days=1) - timedelta(seconds=1)
            except ValueError:
                return Response({'error': 'Invalid date format. Use ISO 8601 format.'}, status=400)
        else:
            return Response({'error': 'Both start and end dates are required.'}, status=400)

        # Query for the top products
        sale_items = SaleItem.objects.select_related('product').filter(
            sale__sale_date__range=[start_date, end_date]
        ).values('product').annotate(
            total_items=Sum('item_qty'),
            total_price=Sum(F('product_price') * F('item_qty'))
        ).order_by('-total_price')[:limit]

        # Prepare the response data
        response_data = []
        for item in sale_items:
            product = Product.objects.get(id=item['product'])
            response_data.append({
                'Product_id': product.id,
                'Product_code': product.product_code,
                'product_name': product.product_name,
                'total_items': item['total_items'],
                'total_price': item['total_price']
            })

        return Response({
            'params': {
                'data_periode_start': start_date.isoformat(),
                'data_periode_end': end_date.isoformat(),
                'total_data_show': limit
            },
            'data': response_data
        })

        
        
        