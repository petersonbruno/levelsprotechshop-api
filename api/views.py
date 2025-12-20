from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.paginator import Paginator
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from .models import Product, ProductImage
from .serializers import ProductSerializer, ProductCreateSerializer, ProductImageSerializer
from .utils import success_response, error_response, validate_image_file
import logging

logger = logging.getLogger(__name__)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Product instances.
    Supports filtering, search, pagination, and sorting.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def get_permissions(self):
        """Require authentication for create, update, and delete operations."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'delete_image']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get_serializer_class(self):
        """Use different serializer for create/update operations."""
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        return ProductSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = Product.objects.all()
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Search by name (case-insensitive)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        # Filter by trending
        trending = self.request.query_params.get('trending', None)
        if trending is not None:
            # Accept 'true', 'True', '1', 'yes', 'on' as True, anything else as False
            trending_bool = trending.lower() in ('true', '1', 'yes', 'on')
            queryset = queryset.filter(trending=trending_bool)
        
        # Sorting
        sort_by = self.request.query_params.get('sort', None)
        if sort_by:
            if sort_by == 'name':
                queryset = queryset.order_by('name')
            elif sort_by == '-name':
                queryset = queryset.order_by('-name')
            elif sort_by == 'price':
                # For price sorting, we'll sort in Python after fetching
                # This is because price is stored as string "950,000 TZS"
                queryset = list(queryset)
                queryset.sort(key=lambda p: self._extract_price_value(p.price))
            elif sort_by == '-price':
                queryset = list(queryset)
                queryset.sort(key=lambda p: self._extract_price_value(p.price), reverse=True)
            elif sort_by == 'date':
                queryset = queryset.order_by('created_at')
            elif sort_by == '-date':
                queryset = queryset.order_by('-created_at')
        else:
            # Default sorting by date (newest first)
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def _extract_price_value(self, price_str):
        """Extract numeric value from price string for sorting."""
        try:
            # Remove 'TZS' and commas, then convert to float
            numeric_str = price_str.replace('TZS', '').replace(',', '').strip()
            return float(numeric_str)
        except:
            return 0.0
    
    def list(self, request, *args, **kwargs):
        """List all products with pagination."""
        try:
            queryset = self.get_queryset()
            
            # Check if queryset is a list (for price sorting)
            is_list = isinstance(queryset, list)
            
            # Pagination
            limit = int(request.query_params.get('limit', 20))
            offset = int(request.query_params.get('offset', 0))
            
            # Validate pagination params
            if limit < 1 or limit > 100:
                limit = 20
            if offset < 0:
                offset = 0
            
            if is_list:
                # Manual pagination for list
                total_count = len(queryset)
                start = offset
                end = offset + limit
                paginated_items = queryset[start:end]
                total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
            else:
                # Django pagination for queryset
                paginator = Paginator(queryset, limit)
                page_number = (offset // limit) + 1
                page_obj = paginator.get_page(page_number)
                paginated_items = page_obj
                total_count = paginator.count
                total_pages = paginator.num_pages
            
            serializer = self.get_serializer(paginated_items, many=True)
            
            return success_response(
                data={
                    'products': serializer.data,
                    'count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'total_pages': total_pages
                },
                message="Products retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error listing products: {str(e)}")
            return error_response(
                "Failed to retrieve products",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, *args, **kwargs):
        """Get a single product by ID."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return success_response(
                data=serializer.data,
                message="Product retrieved successfully"
            )
        except Product.DoesNotExist:
            return error_response(
                "Product not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving product: {str(e)}")
            return error_response(
                "Failed to retrieve product",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        """Create a new product."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Set creator to the authenticated user
            product = serializer.save(creator=request.user)
            
            # Handle image file uploads
            if 'images' in request.FILES:
                images = request.FILES.getlist('images')
                if len(images) > 10:
                    product.delete()
                    return error_response(
                        "Maximum 10 images allowed per product",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                for image_file in images:
                    try:
                        validate_image_file(image_file)
                        ProductImage.objects.create(product=product, image=image_file)
                    except ValueError as e:
                        product.delete()
                        return error_response(
                            str(e),
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
            
            # Validate at least one image exists
            if product.images.count() == 0:
                product.delete()
                return error_response(
                    "At least one image is required",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            response_serializer = ProductSerializer(product, context={'request': request})
            return success_response(
                data=response_serializer.data,
                message="Product created successfully",
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            if hasattr(e, 'detail'):
                return error_response(
                    str(e.detail),
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            return error_response(
                "Failed to create product",
                details=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, *args, **kwargs):
        """Update an existing product."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            
            # Handle new image file uploads
            if 'images' in request.FILES:
                images = request.FILES.getlist('images')
                current_count = instance.images.count()
                if current_count + len(images) > 10:
                    return error_response(
                        f"Maximum 10 images allowed. Currently have {current_count} images.",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                for image_file in images:
                    try:
                        validate_image_file(image_file)
                        ProductImage.objects.create(product=instance, image=image_file)
                    except ValueError as e:
                        return error_response(
                            str(e),
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
            
            product = serializer.save()
            response_serializer = ProductSerializer(product, context={'request': request})
            return success_response(
                data=response_serializer.data,
                message="Product updated successfully"
            )
        except Product.DoesNotExist:
            return error_response(
                "Product not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error updating product: {str(e)}")
            if hasattr(e, 'detail'):
                return error_response(
                    str(e.detail),
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            return error_response(
                "Failed to update product",
                details=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    def partial_update(self, request, *args, **kwargs):
        """Partially update an existing product."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            # Handle new image file uploads
            if 'images' in request.FILES:
                images = request.FILES.getlist('images')
                current_count = instance.images.count()
                if current_count + len(images) > 10:
                    return error_response(
                        f"Maximum 10 images allowed. Currently have {current_count} images.",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )
                
                for image_file in images:
                    try:
                        validate_image_file(image_file)
                        ProductImage.objects.create(product=instance, image=image_file)
                    except ValueError as e:
                        return error_response(
                            str(e),
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
            
            product = serializer.save()
            response_serializer = ProductSerializer(product, context={'request': request})
            return success_response(
                data=response_serializer.data,
                message="Product updated successfully"
            )
        except Product.DoesNotExist:
            return error_response(
                "Product not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error updating product: {str(e)}")
            if hasattr(e, 'detail'):
                return error_response(
                    str(e.detail),
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            return error_response(
                "Failed to update product",
                details=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a product by ID."""
        try:
            instance = self.get_object()
            instance.delete()
            return success_response(
                data=None,
                message="Product deleted successfully"
            )
        except Product.DoesNotExist:
            return error_response(
                "Product not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting product: {str(e)}")
            return error_response(
                "Failed to delete product",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        """Delete a specific product image."""
        try:
            product = self.get_object()
            image = ProductImage.objects.get(id=image_id, product=product)
            
            # Don't allow deleting if it's the last image
            if product.images.count() <= 1:
                return error_response(
                    "Cannot delete the last image. At least one image is required.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            image.delete()
            return success_response(
                message="Image deleted successfully"
            )
        except ProductImage.DoesNotExist:
            return error_response(
                "Image not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting image: {str(e)}")
            return error_response(
                "Failed to delete image",
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def health_check(request):
    """Health check endpoint."""
    return success_response(
        data={'status': 'healthy'},
        message="API is running successfully"
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Simple login API with username and password."""
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return error_response(
                "Username and password are required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is None:
            return error_response(
                "Invalid username or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get or create token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        return success_response(
            data={
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email if hasattr(user, 'email') else None
            },
            message="Login successful"
        )
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return error_response(
            "Failed to login",
            details=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _extract_price_value(price_str):
    """Extract numeric value from price string for sorting."""
    try:
        # Remove 'TZS' and commas, then convert to float
        numeric_str = price_str.replace('TZS', '').replace(',', '').strip()
        return float(numeric_str)
    except:
        return 0.0


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Dashboard endpoint for product creators to view their products."""
    try:
        user = request.user
        
        # Get all products created by the user
        queryset = Product.objects.filter(creator=user)
        
        # Apply filtering, search, and sorting (similar to ProductViewSet)
        category = request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        # Filter by trending
        trending = request.query_params.get('trending', None)
        if trending is not None:
            # Accept 'true', 'True', '1', 'yes', 'on' as True, anything else as False
            trending_bool = trending.lower() in ('true', '1', 'yes', 'on')
            queryset = queryset.filter(trending=trending_bool)
        
        sort_by = request.query_params.get('sort', None)
        if sort_by:
            if sort_by == 'name':
                queryset = queryset.order_by('name')
            elif sort_by == '-name':
                queryset = queryset.order_by('-name')
            elif sort_by == 'price':
                queryset = list(queryset)
                queryset.sort(key=lambda p: _extract_price_value(p.price))
            elif sort_by == '-price':
                queryset = list(queryset)
                queryset.sort(key=lambda p: _extract_price_value(p.price), reverse=True)
            elif sort_by == 'date':
                queryset = queryset.order_by('created_at')
            elif sort_by == '-date':
                queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        # Pagination
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        
        if limit < 1 or limit > 100:
            limit = 20
        if offset < 0:
            offset = 0
        
        is_list = isinstance(queryset, list)
        
        if is_list:
            total_count = len(queryset)
            start = offset
            end = offset + limit
            paginated_items = queryset[start:end]
            total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
        else:
            paginator = Paginator(queryset, limit)
            page_number = (offset // limit) + 1
            page_obj = paginator.get_page(page_number)
            paginated_items = page_obj
            total_count = paginator.count
            total_pages = paginator.num_pages
        
        serializer = ProductSerializer(paginated_items, many=True, context={'request': request})
        
        return success_response(
            data={
                'products': serializer.data,
                'count': total_count,
                'limit': limit,
                'offset': offset,
                'total_pages': total_pages,
                'creator': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email if hasattr(user, 'email') else None
                }
            },
            message="Dashboard data retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving dashboard: {str(e)}")
        return error_response(
            "Failed to retrieve dashboard data",
            details=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


