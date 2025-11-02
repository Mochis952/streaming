import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from . import services

@csrf_exempt
@require_http_methods(["POST"])
def start_new_session_view(request):
    """
    API view to initiate a new Facebook login process and save the session.
    Expects a JSON body with 'account_id' and 'password'.
    """
    try:
        data = json.loads(request.body)
        account_id = "german04@live.com.mx"
        password = "juegos123"

        if not account_id or not password:
            return JsonResponse({'status': 'error', 'message': 'account_id and password are required.'}, status=400)

        success = services.login_and_save_session(account_id, password)

        if success:
            return JsonResponse({'status': 'success', 'message': f'Session saved for {account_id}.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to log in and save session. Check logs for details.'}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON body.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def load_existing_session_view(request):
    """
    API view to load an existing Facebook session into a Selenium driver.
    Expects an 'account_id' as a query parameter.
    This is a demonstrative view; it initializes a driver and then closes it.
    """
    account_id = request.GET.get('account_id')

    if not account_id:
        return JsonResponse({'status': 'error', 'message': 'account_id query parameter is required.'}, status=400)

    # In a real application, you would take the driver and do something with it.
    # For this example, we just confirm it works and then quit.
    driver = services.get_driver_with_session(account_id)

    if driver:
        try:
            page_title = driver.title
            # You could add more actions here, like navigating to a specific page
            # or scraping data, before quitting.
            return JsonResponse({'status': 'success', 'message': f'Session for {account_id} loaded successfully. Page title: {page_title}'})
        finally:
            driver.quit()
    else:
        return JsonResponse({'status': 'error', 'message': f'Could not load session for {account_id}.'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def create_listing_view(request):
    """
    API view to create a new Facebook Marketplace listing.
    Expects a JSON body with 'account_id' and 'listing_data'.
    """
    try:
        data = json.loads(request.body)
        account_id = data.get('account_id')
        listing_data = data.get('listing_data')

        if not account_id or not listing_data:
            return JsonResponse({'status': 'error', 'message': 'account_id and listing_data are required.'}, status=400)

        result = services.create_marketplace_listing(account_id, listing_data)

        if result.get('status') == 'success':
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON body.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_categories_view(request):
    """
    API view to get Facebook Marketplace categories.
    Expects an 'account_id' as a query parameter.
    """
    account_id = request.GET.get('account_id')
    listing_id = request.GET.get('listing_id', '0') # Default to 0 if not provided

    if not account_id:
        return JsonResponse({'status': 'error', 'message': 'account_id query parameter is required.'}, status=400)

    result = services.get_marketplace_categories(account_id, listing_id)

    if result.get('status') == 'error':
        return JsonResponse(result, status=404)
    else:
        return JsonResponse(result)
