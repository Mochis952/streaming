import time
import json
import logging
import os
import random
import re
from urllib.parse import quote

import requests
from decouple import config
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .models import FacebookSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_driver():
    """Initializes and returns a Selenium Chrome driver."""
    options = ChromeOptions()
    # options.add_argument('--headless=new') # Running in headless mode can be detected by Facebook
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def login_and_save_session(account_id, password):
    """
    Logs into Facebook using Selenium, extracts session cookies, and saves them
    to the database.

    Args:
        account_id (str): The Facebook username or email.
        password (str): The Facebook password.

    Returns:
        bool: True if login and session saving were successful, False otherwise.
    """
    driver = _get_driver()
    try:
        logger.info(f"Attempting to log in as {account_id}")
        driver.get('https://www.facebook.com')
        time.sleep(2) # Allow page to load

        # Find and fill login form
        email_input = driver.find_element(By.ID, 'email')
        pass_input = driver.find_element(By.ID, 'pass')
        email_input.send_keys(account_id)
        time.sleep(1)
        pass_input.send_keys(password)
        time.sleep(1)
        
        # Click login button
        login_button = driver.find_element(By.NAME, 'login')
        time.sleep(10)
        login_button.click()
        time.sleep(5) # Wait for login to process and redirect

        # Check for login success (a simple check, might need improvement)
        if "login/device-based/regular/password/" in driver.current_url:
            logger.error("Login failed. Check credentials or 2FA.")
            return False

        logger.info("Login successful. Extracting cookies.")

        # Extract cookies
        all_cookies = driver.get_cookies()
        session_cookies = {
            cookie['name']: cookie['value'] 
            for cookie in all_cookies 
            if cookie['name'] in ['c_user', 'xs', 'datr', 'fr', 'sb', 'wd']
        }

        if 'c_user' not in session_cookies or 'xs' not in session_cookies:
            logger.error("Could not find essential session cookies (c_user, xs). Login may have failed.")
            return False

        # Go to a page to get the f_value
        driver.get('https://www.facebook.com/marketplace/mexicocity')
        time.sleep(3)
        f_value = None
        try:
            script_element = driver.execute_script("return document.getElementById('__eqmc')")
            if script_element:
                data = driver.execute_script("return JSON.parse(arguments[0].innerHTML)", script_element)
                f_value = data.get('f')
        except Exception as e:
            logger.warning(f"Could not extract f_value: {e}")

        if not f_value:
            logger.warning("f_value not found. Some API calls might fail.")

        # Save to database
        session, created = FacebookSession.objects.update_or_create(
            account_id=account_id,
            defaults={
                'cookies': session_cookies,
                'f_value': f_value or ''
            }
        )
        logger.info(f"Facebook session for {account_id} has been {'created' if created else 'updated'}.")
        return True

    except Exception as e:
        logger.error(f"An error occurred during Facebook login: {e}")
        return False
    finally:
        driver.quit()

def get_driver_with_session(account_id):
    """
    Retrieves a saved Facebook session and initializes a Selenium driver with it.

    Args:
        account_id (str): The account_id of the session to load.

    Returns:
        webdriver.Chrome: An authenticated Selenium driver, or None if session not found.
    """
    try:
        session = FacebookSession.objects.get(account_id=account_id)
        logger.info(f"Found session for {account_id}. Initializing driver.")
    except FacebookSession.DoesNotExist:
        logger.error(f"No session found for account_id: {account_id}")
        return None

    driver = _get_driver()
    try:
        # Selenium requires visiting the domain before adding cookies
        driver.get("https://www.facebook.com/")
        time.sleep(1)

        for name, value in session.cookies.items():
            cookie = {'name': name, 'value': value, 'domain': '.facebook.com'}
            driver.add_cookie(cookie)
        
        logger.info("Cookies added to the driver. Refreshing page.")
        driver.refresh()
        time.sleep(3) # Wait for page to load with cookies

        # Verify login by checking for a key element, e.g., profile name
        try:
            profile_element = driver.find_element(By.XPATH, "//a[contains(@href, '/me/') or contains(@href, '/profile.php')]")
            logger.info(f"Session restored successfully. Profile element found: {profile_element.text}")
            return driver
        except:
            logger.error("Failed to verify session. The cookies might be expired or invalid.")
            driver.quit()
            return None

    except Exception as e:
        logger.error(f"An error occurred while loading the session into the driver: {e}")
        driver.quit()
        return None

def create_marketplace_listing(account_id, listing_data):
    """
    Creates a new listing in Facebook Marketplace.

    Args:
        account_id (str): The account_id of the session to use.
        listing_data (dict): A dictionary containing the listing information.

    Returns:
        dict: A dictionary with the result of the operation.
    """
    try:
        session = FacebookSession.objects.get(account_id=account_id)
        logger.info(f"Found session for {account_id}.")
    except FacebookSession.DoesNotExist:
        logger.error(f"No session found for account_id: {account_id}")
        return {'status': 'error', 'message': f'No session found for account_id: {account_id}'}

    def img_uploader(num_img, file_img_path):
        url = "https://upload.facebook.com/ajax/react_composer/attachments/photo/upload?__a=1"

        payload = {'fb_dtsg': session.f_value,
        'source': '8',
        'profile_id': session.cookies['c_user']}
        files=[
        ('farr',(f'master_0_image_{num_img}.png',open(file_img_path,'rb'),'image/png'))
        ]
        headers = {
        'authority': 'upload.facebook.com',
        'accept': '*/*',
        'accept-language': 'es-419,es;q=0.9',
        'cookie': f"sb={session.cookies['sb']}; c_user={session.cookies['c_user']}; datr={session.cookies['datr']}; xs={session.cookies['xs']}; fr={session.cookies['fr']}; wd={session.cookies['wd']}",
        'origin': 'https://www.facebook.com',
        'referer': 'https://www.facebook.com/',
        'sec-ch-ua': '"Brave";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
        }

        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        content = response.content
        content = content.decode('utf-8')
        content = str(content)
        start_index = content.find('{')
        if start_index != -1:
            content = content[start_index:]

        content = json.loads(content)
        logger.debug(f"Response from image uploader for {listing_data['title']}: {content}")

        if 'error' in content:
            logger.error("Error uploading photo to Facebook")
            return ''
        
        photo_id = content['payload']['photoID']

        return photo_id

    def create_master(photos_ids, title, description, latitude, longitude, article_id, groups_ids=None):
        description = f"{description}\n\n{config('DELIVERY_INFO')}"
        plain_title = title.replace('"', '\\"')
        photos_ids_formatted = '%2C'.join(f'%22{element}%22' for element in photos_ids)

        if groups_ids is not None:
            groups_ids = groups_ids.strip("[]").split(",")
            groups_ids_formatted = '%2C'.join(f'%22{element}%22' for element in groups_ids) 
        else:
            groups_ids_formatted = ''
            
        time.sleep(5)
        
        common_data = {
            "category_id": listing_data['category'],
            "commerce_shipping_carrier": None,
            "commerce_shipping_carriers": [],
            "comparable_price": None,
            "cost_per_additional_item": None,
            "delivery_types": ["IN_PERSON", "PUBLIC_MEETUP"],
            "description": {"text": description},
            "draft_type": None,
            "hidden_from_friends_visibility": "VISIBLE_TO_EVERYONE",
            "is_personalization_required": None,
            "is_photo_order_set_by_seller": False,
            "is_preview": False,
            "item_price": {"currency": "MXN", "price": listing_data['price']},
            "latitude": latitude,
            "listing_email_id": None,
            "longitude": longitude,
            "min_acceptable_checkout_offer_price": None,
            "personalization_info": None,
            "product_hashtag_names": listing_data['hashtags'].split(',') if listing_data['hashtags'] else [],
            "quantity": -1,
            "shipping_calculation_logic_version": None,
            "shipping_cost_option": "BUYER_PAID_SHIPPING",
            "shipping_cost_range_lower_cost": None,
            "shipping_cost_range_upper_cost": None,
            "shipping_label_price": "0",
            "shipping_label_rate_code": None,
            "shipping_label_rate_type": None,
            "shipping_offered": False,
            "shipping_options_data": [],
            "shipping_package_weight": None,
            "shipping_price": None,
            "shipping_service_type": None,
            "sku": article_id,
            "source_type": "composer_listing_type_selector",
            "suggested_hashtag_names": [],
            "surface": "composer",
            "title": title,
            "variants": [],
            "video_ids": [],
            "xpost_target_ids": groups_ids_formatted,
            "photo_ids": photos_ids
        }

        input_data = {
            "client_mutation_id": "8",
            "actor_id": session.cookies['c_user'],
            "attribution_id_v2": "CometMarketplaceComposerRoot.react,comet.marketplace.composer,unexpected,1753743463490,933400,1606854132932955,,;CometMarketplaceComposerRoot.react,comet.marketplace.composer,unexpected,1753743395466,911603,1606854132932955,,;CometMarketplaceComposerCreateComponent.react,comet.marketplace.composer.create,unexpected,1753743377703,634582,1606854132932955,,;CometMarketplaceHomeRoot.react,comet.marketplace.home,tap_bookmark,1753743376191,745342,1606854132932955,,",
            "audience": {"marketplace": {"marketplace_id": "630562697113569"}},
            "data": {"common": common_data}
        }

        variables_encoded = quote(json.dumps({"input": input_data}))

        payload = f'av={session.cookies["c_user"]}&__user={session.cookies["c_user"]}&__a=1&__comet_req=15&fb_dtsg={session.f_value}&variables={variables_encoded}&doc_id=9551550371629242'
        
        headers = {
            'accept': '*/*',
            'accept-language': 'es-419,es;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
            'Cookie': f"sb={session.cookies['sb']}; datr={session.cookies['datr']}; c_user={session.cookies['c_user']}; xs={session.cookies['xs']}; fr={session.cookies['fr']}; wd={session.cookies['wd']}",
            'origin': 'https://www.facebook.com',
            'priority': 'u=1, i',
            'referer': 'https://www.facebook.com/marketplace/create/item?step=audience',
            'sec-ch-ua': '"Brave";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            'sec-ch-ua-full-version-list': '"Brave";v="129.0.0.0", "Not=A?Brand";v="8.0.0.0", "Chromium";v="129.0.0.0"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"macOS"',
            'sec-ch-ua-platform-version': '"14.0.0"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'x-asbd-id': '359341',
            'x-fb-friendly-name': 'useCometMarketplaceListingCreateMutation',
            'x-fb-lsd': 'je8E3u-NI9fP1U4ayAO3kP'
        }

        response = requests.request("POST", "https://www.facebook.com/api/graphql/", headers=headers, data=payload)
        content = response.content
        content = content.decode('utf-8')
        content = json.loads(content)
        logger.debug(f"Response from create master for {title}: {content}")

        if 'errors' in content:
            logger.error("Could not create listing")
            return 0, "", 0
        
        content_id = content["data"]["marketplace_listing_create"]["listing"]["id"]
        
        return content_id, plain_title, listing_data['price']
    
    article_id = listing_data["article_id"]
    title = listing_data["title"]
    category = listing_data["category"]
    price = listing_data["price"]
    condition = listing_data["condition"]
    brand = listing_data["brand"]
    latitude = listing_data["latitude"]
    longitude = listing_data["longitude"]
    description = listing_data["description"]
    groups_ids = listing_data["groups_ids"]
    img_urls = listing_data["images_urls"]
    hashtags = listing_data.get("hashtags", "")

    if isinstance(img_urls, str):
        try:
            img_urls = json.loads(img_urls)
        except json.JSONDecodeError:
            return {'status': 'error', 'message': 'Invalid JSON string for image URLs'}
    
    list_img_path = []
    base_dir_img_market = os.path.expanduser("~/Documents/Imágenes_Market")
    os.makedirs(base_dir_img_market, exist_ok=True)
    num_title_img = random.randint(1, 100)

    for x, item in enumerate(img_urls):
        image = item
        download_image = requests.get(image)
        file_img_fb_path = os.path.join(base_dir_img_market, f"{account_id}_master_{num_title_img}_image_{x}.png")

        with open(file_img_fb_path, 'wb') as img:
            img.write(download_image.content)

        list_img_path.append(file_img_fb_path)

    photos_ids = []

    for x, img in enumerate(list_img_path):
        time.sleep(3)
        photo_id = img_uploader(x, img)
        photos_ids.append(photo_id)

    time.sleep(3)
    create_response_id, title_master, price_master = create_master(photos_ids, title, description, latitude, longitude, article_id, groups_ids)

    if create_response_id == 0:
        return {'status': 'error', 'message': 'Failed to create listing'}
    else:
        # Clean up downloaded images
        for img_path in list_img_path:
            os.remove(img_path)
            
        return {'status': 'success', 'listing_id': create_response_id, 'title': title_master, 'price': price_master}

def get_marketplace_categories(account_id, listing_id):
    """
    Retrieves the marketplace categories and conditions.

    Args:
        account_id (str): The account_id of the session to use.
        listing_id (str): A valid listing ID to use for the query.

    Returns:
        dict: A dictionary with the categories and conditions.
    """
    try:
        session = FacebookSession.objects.get(account_id=account_id)
        logger.info(f"Found session for {account_id}.")
    except FacebookSession.DoesNotExist:
        logger.error(f"No session found for account_id: {account_id}")
        return {'status': 'error', 'message': f'No session found for account_id: {account_id}'}

    payload = f'fb_dtsg={session.f_value}&variables=%7B%22category_id%22%3A%220%22%2C%22composer_mode%22%3A%22EDIT_LISTING%22%2C%22delivery_types%22%3A%5B%22in_person%22%2C%22public_meetup%22%5D%2C%22has_prefetched_category%22%3Afalse%2C%22has_prefill_data%22%3Afalse%2C%22is_edit%22%3Atrue%2C%22listingId%22%3A%22{listing_id}%22%2C%22prefill_id%22%3A%220%22%2C%22scale%22%3A1%7D&doc_id=9625321710843690'
    headers = {
    'authority': 'www.facebook.com',
    'accept': '*/*',
    'accept-language': 'es-419,es;q=0.6',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://www.facebook.com',
    'cookie': f"sb={session.cookies['sb']}; c_user={session.cookies['c_user']}; datr={session.cookies['datr']}; xs={session.cookies['xs']}; fr={session.cookies['fr']}; wd={session.cookies['wd']}",
    'referer': 'https://www.facebook.com/marketplace/you/selling',
    'sec-ch-ua': '"Brave";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-ch-ua-platform-version': '"10.15.0"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'x-asbd-id': '129477',
    'x-fb-friendly-name': 'CometMarketplaceComposerRootComponentQuery',
    'x-fb-lsd': 'mmblakC_5tbmiu6gjJYYmF'
    }

    response = requests.request("POST", "https://www.facebook.com/api/graphql/", headers=headers, data=payload)
    content = response.content
    content = content.decode('utf-8')
    content = json.loads(content)
    
    categories = content['data']['viewer']['marketplace_categories']
    condition = content['data']['viewer']['marketplace_composer_fields']

    return {'categories': categories, 'conditions': condition}
