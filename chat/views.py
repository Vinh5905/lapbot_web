from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.forms.models import model_to_dict
from chat.models import LaptopInfo
import json
import re
import requests
import markdown
from .predictor_service import predictor # Import instance đã được tải sẵn trong apps
from .llms_service import llms
from .form_predict import LaptopPredictionFeaturesForm
from .prompts import SYSTEM_CONTENT_USER_MESS_EXTRACT_AND_GEN_GROUP, SYSTEM_CONTENT_INTENT_OTHERS, SYSTEM_CONTENT_INTENT_FIND, SYSTEM_CONTENT_INTENT_DETECT

# Markdown
md = markdown.Markdown(extensions=["fenced_code"])

def extract_json_from_string(text: str) -> str | None:
    """
    Trích xuất chuỗi JSON từ bên trong một khối mã Markdown.
    """
    # Regex tương tự, nhưng không có dấu / ở đầu và cuối
    # re.DOTALL cho phép `.` khớp với cả ký tự xuống dòng, tương đương [\s\S]
    pattern = r"```(?:json)?\s*(.*?)\s*```"
    
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        # group(1) là capturing group đầu tiên
        return match.group(1).strip()
    
    # Nếu không tìm thấy, trả về chuỗi gốc để thử parse
    return text.strip()

# VIEW 
@csrf_exempt
def index(request):
    """
    Hiển thị trang chat chính.
    """ 
    # Khởi tạo nếu chưa có
    chat_history = request.session.get('chat_history', [])

    return render(request, 'chat/index.html', {
        'chat_history': chat_history
    })

@csrf_exempt
def intent_detect(request):
    """
    Model trả về intent message của người dùng để phân cách trả lời
    """
    intent_type = {
        0: 'Find laptop',
        1: 'Others',
    }

    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            user_message = data.get('user_message', '')

            intent = int(llms.invoke(SYSTEM_CONTENT_INTENT_DETECT, user_message))

            return JsonResponse({
                'data_intent': {
                    'intent_code': intent,
                    'intent_meaning': intent_type[intent]
                }
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            print(f"Error processing message: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)

    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def send_message(request):
    """
    Xử lý tin nhắn từ người dùng (gửi qua AJAX POST request).
    Lấy phản hồi từ bot và trả về dưới dạng JSON.
    """
    if request.method == 'POST':
        try:
            # Lấy dữ liệu JSON từ body của request
            # Cần đảm bảo client gửi Content-Type: application/json
            data = json.loads(request.body.decode('utf-8'))
            user_message = data.get('user_message', '')

            if not user_message:
                return JsonResponse({
                    'status': 400,
                    'error': 'Message cannot be empty!'
                }, status=400)
            
            intent_detect_url = 'http://localhost:8000/chat/intent_detect/'
            try:
                resp = requests.post(intent_detect_url, json=data)
                resp.raise_for_status() 
                data = resp.json()  
                intent = data.get('data_intent')  # dict chứa intent_code, intent_meaning
            except Exception as e:
                print(f"Error calling send_message API: {e}")   
                raise e

            if intent['intent_code'] == 0:
                response = llms.invoke(SYSTEM_CONTENT_USER_MESS_EXTRACT_AND_GEN_GROUP, user_message)
                print(response)
                response = extract_json_from_string(response)
                response = json.loads(response) # Chuyển về dict
                data_result = []

                predict_price_url = 'http://localhost:8000/chat/predict_price/'

                for item in response:
                    recommendation = {}

                    persona = item.get("persona", None)
                    filters = item.get("filters", {})

                    if (not persona) or (not filters):
                        continue

                    try:
                        resp = requests.post(predict_price_url, json={
                            'data': item['prediction_profile']
                        })
                        resp.raise_for_status() 
                        data = resp.json()  
                        predict_price = data.get('predict_price')  # dict chứa intent_code, intent_meaning
                    except Exception as e:
                        print(f"Error calling predict price API: {e}")   
                        raise e
                    
                    try:
                        # Dùng **filters để "giải nén" dictionary thành các tham số cho .filter()
                        laptop_filters = LaptopInfo.objects.filter(**filters)\
                                                                .values('url_path', 'image', 'root_price', 'discounted_price', 'name', 
                                                                        'laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong', 
                                                                        'hoc_tap_van_phong', 'mong_nhe', 'gaming')\
                                                                .order_by('discounted_price') # Lấy 5 kết quả hàng đầu
                        suggested_laptops = list(laptop_filters)
                        
                        usage_keys = [
                            'laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong', 
                            'hoc_tap_van_phong', 'mong_nhe', 'gaming'
                        ]

                        usage_keys_alias = {
                            'laptop_sang_tao_noi_dung': 'Sáng tạo nội dung',
                            'do_hoa_ky_thuat': 'Đồ họa - Kỹ thuật',
                            'cao_cap_sang_trong': 'Cao cấp - Sang trọng',
                            'hoc_tap_van_phong': 'Học tập - Văn phòng',
                            'mong_nhe': 'Mỏng nhẹ',
                            'gaming': 'Gaming'
                        }

                        for laptop in suggested_laptops:
                            laptop['usage_needs'] = [usage_keys_alias[key] for key in usage_keys if laptop.get(key, 0) == 1]
                        
                            # (Tùy chọn) Xóa các key cũ để làm sạch output
                        for key_to_remove in usage_keys:
                            laptop.pop(key_to_remove, None) # .pop(key, None) sẽ không báo lỗi nếu key không tồn tại
                        
                    except Exception as e:
                        # Bắt các lỗi có thể xảy ra do filter không hợp lệ
                        print(f"Lỗi khi thực thi filter cho persona '{persona}': {e}")
                        suggested_laptops = []
                    
                    recommendation['persona'] = persona
                    recommendation['general_price'] = predict_price
                    recommendation['suggested_laptops'] = suggested_laptops

                    data_result.append(recommendation)

            elif intent['intent_code'] == 1:
                response = llms.invoke(SYSTEM_CONTENT_INTENT_OTHERS, user_message)
                data_result = response

            return JsonResponse({
                'data': {
                    **intent,
                    'user_message': user_message,
                    'ai_response': data_result
                }
            }, status=200)

        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        except Exception as e:
            print(f"Error processing message: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)
        
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    

@csrf_exempt
def user_message_html(request):
    if request.method == 'POST':
        try:
            # Lấy dữ liệu JSON từ body của request
            # Cần đảm bảo client gửi Content-Type: application/json
            data = json.loads(request.body.decode('utf-8'))
            data = data.get('data', '')
            user_message = data.get('user_message', '')

            if not user_message:
                return JsonResponse({
                    'status': 400,
                    'error': 'Message cannot be empty!'
                }, status=400)
            
            data_md_converted = {
                "user_message": md.convert(user_message)
            }

            chat_block_html = render_to_string('components/message/user_message.html', {
                "data": data_md_converted
            })

            return JsonResponse({"html": chat_block_html})
        
        except Exception as e:
            print(f"Error processing message: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    

@csrf_exempt
def ai_message_html(request):
    if request.method == 'POST':
        chat_history = request.session.get('chat_history', [])

        try:
            # Lấy dữ liệu JSON từ body của request
            # Cần đảm bảo client gửi Content-Type: application/json
            data = json.loads(request.body.decode('utf-8'))
            data = data.get('data', '')
            user_message = data.get('user_message', '')

            if not user_message:
                return JsonResponse({
                    'status': 400,
                    'error': 'Message cannot be empty!'
                }, status=400)
            
            send_mess_url = 'http://localhost:8000/chat/send_message/'
            try:
                resp = requests.post(send_mess_url, json={
                    'user_message': user_message
                })
                resp.raise_for_status()  # Kiểm tra lỗi HTTP
                data = resp.json()       # Lấy dict JSON từ response
                response = data.get('data')  # Lấy phần data, thay đổi tùy response server
            except Exception as e:
                print(f"Error calling send_message API: {e}")   
                raise e
            
            data_md_converted = {
                'intent_code': response['intent_code'],
                'intent_meaning': response['intent_meaning'],
                'user_message': md.convert(response['user_message']),
                'ai_response': response['ai_response'] if response['intent_code'] == 0 else md.convert(response['ai_response'])
            }

            chat_block_html = render_to_string('components/message/ai_message.html', {
                'data': data_md_converted
            })

            chat_history.append(data_md_converted)
            request.session['chat_history'] = chat_history
            request.session.modified = True 

            return JsonResponse({"html": chat_block_html})
        
        except Exception as e:
            print(f"Error processing message: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def delete_all_message(request):
    if request.method == 'POST':
        try:
            if 'chat_history' in request.session:
                del request.session['chat_history']  # Xóa session
                request.session.modified = True

            return JsonResponse({'status': 'Deleted all messages sucessfully!'}, status=200)
        
        except Exception as e:
            print(f"Error processing message: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
def predict_price(request):
    if request.method == 'POST':

        try:
            data = json.loads(request.body.decode('utf-8'))
            data = data.get('data', '')
            print('COME TO PREDICT PRICE')
            print(data)

            # B1: Phân tách câu hỏi ra các biến, LLMs phân nhóm và thêm biến
            # B2: Dùng điều kiện để lọc (không chỉ có ==)
            
            # obj = LaptopInfo.objects.get(product_id='0220042002813__l265_20250402-105034')
            # data = model_to_dict(obj)

            if not data:
                return JsonResponse({
                    'status': 400,
                    'error': 'Data cannot be empty!'
                }, status=400)
            
            form = LaptopPredictionFeaturesForm(data)  

            if form.is_valid():
                print('PASS FORM VALID')
                cleaned_data = form.cleaned_data
                predict_result = predictor.predict(cleaned_data)
                print('COMPLETE PREDICT')
                # Kiểm tra xem service có trả về lỗi không
                if isinstance(predict_result, str) and ("Error" in predict_result):
                    return JsonResponse({'error': predict_result}, status=500)
                
                return JsonResponse({
                    'data': cleaned_data,
                    'predict_price': float(predict_result['predict_price'])
                }, status=200)
            else:
                return JsonResponse({'error': form.errors}, status=400)
            
        except Exception as e:
            print(f"Error processing message: {e}")
            return JsonResponse({'error': 'An internal server error occurred'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)