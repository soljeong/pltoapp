from django.http import JsonResponse
from django.shortcuts import render
from django.core.cache import cache
from django.http import HttpResponse
import requests

from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일 로드

# 환경 변수에서 API 키, 이메일, 비밀번호 가져오기
API_KEY = os.getenv('PLTO_API_KEY')
EMAIL = os.getenv('PLTO_ID')
PASSWORD = os.getenv('PLTO_PW')

if not API_KEY or not EMAIL or not PASSWORD:
    raise ValueError("API_KEY, EMAIL, and PASSWORD must be set in the environment variables.")


BASE_URL = "https://openapi.playauto.io/api"


# API 토큰 발급 함수
def get_token(api_key, email, password):
    url = f"{BASE_URL}/auth"
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "x-api-key": api_key,
    }
    body = {
        "email": email,
        "password": password,
    }
    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        data = response.json()[0]
        return data.get("token")
    else:
        return None

# 주문 리스트 조회 함수
def get_order_list(api_key, token, search_word):
    url = f"{BASE_URL}/orders"
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "x-api-key": api_key,
        "Authorization": f"Token {token}",
    }
    body = {
        "sdate": "2024-01-01",  # 예시 시작일
        "edate": "2024-12-31",  # 예시 종료일
        "start": 0,
        "length": 500,
        "date_type": "wdate",
        "status": ["ALL"],
        "multi_type": "invoice_no",
        "multi_search_word": search_word,
    }
    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Render the homepage
def home(request):

    return render(request, 'home.html')

def result(request):
    user_input = request.POST.get('user_input', '')

    # 캐시에서 토큰을 가져옴
    token = cache.get('api_token')

    # 캐시에 토큰이 없으면 새로 발급받음
    if not token:


        token = get_token(API_KEY, EMAIL, PASSWORD)

        if token:
            # 발급 받은 토큰을 캐시에 저장 (예: 1시간 동안 유효)
            cache.set('api_token', token, timeout=3600)
        else:
            return HttpResponse("API 토큰 발급 실패. 설정을 확인하세요.")

    # API 호출
    order_data = get_order_list(API_KEY, token, user_input)
    order_table = process_data(order_data)

    
    if order_data:
        context = {
            'response_message': f"조회 결과: {order_data['recordsTotalCount']} 건",
            'order_table': order_table,
            'user_input': user_input,
        }
    else:
        context = {
            'response_message': "주문 리스트 조회 실패. 입력값을 확인하세요.",
            'user_input': user_input,
        }

    return render(request, 'result.html', context)


import json
from collections import defaultdict

def json_to_dict(json_data):
    try:
        results = json_data.get("results", [])
        results_prod = json_data.get("results_prod", [])
        
        if not isinstance(results_prod, list):
            print("results_prod 데이터가 예상과 다른 형식입니다.")
            results_prod = []
        
        return results, results_prod
    except Exception as e:
        print("데이터 변환 중 오류 발생:", e)
        return [], []

def fill_missing_values(results, results_prod):
    try:
        prod_dict = {item['uniq']: item for item in results_prod}
        
        for item in results:
            if item.get('map_yn') == 1 and (not item.get('set_cd') or not item.get('set_name')):
                prod_info = prod_dict.get(item['uniq'])
                if prod_info:
                    item['set_cd'] = prod_info.get('sku_cd')
                    item['set_name'] = prod_info.get('prod_name')
        
        return results
    except Exception as e:
        print(f"데이터 가공 중 오류 발생: {e}")
        return results

def process_data(order_list):

    # results와 results_prod 배열 추출
    results = order_list.get('results', [])
    results_prod = order_list.get('results_prod', [])

    # uniq 필드를 키로 사용하여 results를 딕셔너리로 변환
    results_dict = {item['uniq']: item for item in results}

    # 조인된 데이터를 저장할 리스트
    joined_data = []

    # results_prod의 각 항목에 대해 results와 조인
    for prod in results_prod:
        uniq = prod.get('uniq')
        if uniq in results_dict:
            joined_item = {**results_dict[uniq], **prod}
            joined_data.append(joined_item)

    # 필요한 필드만 추출하여 리스트로 변환
    return [(item['shop_sale_name'], item['sku_cd'], item['stock_cd'], item['stock_cnt_real']) for item in joined_data]



