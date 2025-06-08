from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from chat.models import LaptopInfo
from together import Together
import json
import os
import dotenv
import requests
import markdown

# Markdown
md = markdown.Markdown(extensions=["fenced_code"])

# LLMs
dotenv.load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

client = Together(api_key=TOGETHER_API_KEY)

def message_llms(system_content, query):
    message = [
        {
            "role": "system",
            "content": system_content
        },
        {
            "role": "user",
            "content": f'''
                Câu dưới đây chính là INPUT của người dùng: \n
                { query }
            '''
        }
    ]

    return message

def chat(message):
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=message,
        temperature=0.0
    )

    return response.choices[0].message.content

system_content_intent_find = '''
    Bạn là một chuyên gia tư vấn laptop. Dựa trên yêu cầu tìm kiếm laptop của người dùng, hãy tạo ra một danh sách các nhóm sản phẩm phù hợp. Mỗi nhóm sẽ đại diện cho một phân khúc hoặc mục đích sử dụng cụ thể mà các thông số người dùng đưa ra có thể đáp ứng.\n

    **Yêu cầu đầu vào của người dùng:** Một câu hỏi để tìm kiếm laptop với một vài thông tin có sẵn\n

    **Nhiệm vụ:**\n
    Phân tích yêu cầu của người dùng. Tự động xác định các nhóm (phân khúc/mục đích sử dụng) phù hợp dựa trên các thông số kỹ thuật được cung cấp (ví dụ: RAM, dung lượng lưu trữ, có thể ngầm hiểu thêm về giá cả nếu người dùng đề cập) và kiến thức chung về thị trường laptop.\n
    Với mỗi nhóm được xác định, hãy cung cấp thông tin chi tiết.\n

    **Định dạng Output (JSON):**\n
    Giá chỉ cần con số, không cần loại đơn vị tiền tệ.\n
    Chỉ trả về một danh sách (array) các đối tượng JSON và không ghi thêm bất cứ thứ gì. Mỗi đối tượng đại diện cho một nhóm sản phẩm và phải tuân thủ cấu trúc sau:\n

    ```json\n
    [\n
    {\n
        "group": "string", // Tên nhóm tự xác định, ví dụ: "Laptop Gaming Tầm Trung", "MacBook Cho Sinh Viên Sáng Tạo", "Laptop Văn Phòng Hiệu Năng Cao"\n
        "general_price": "string", // Mô tả giá trung bình với nhóm này, ví dụ "18.000.000", "25.500.000", tuyệt đối KHÔNG ghi theo dạng (18.000.000 - 25.000.000)\n
        "suggested_laptops": [\n
        {\n
            "name": "string", // Tên đầy đủ của sản phẩm, ví dụ: "Laptop Gaming Acer Nitro V ANV15-51-57B2 i5 13420H/16GB/512GB/RTX4050", "MacBook Pro 14 inch M3 Pro 11CPU 14GPU 18GB 512GB"\n
            "current_price": "string", // Giá bán hiện tại của sản phẩm (bao gồm đơn vị tiền tệ, ví dụ: "22.990.000")\n
            "old_price": "string", // Giá gốc trước khi giảm (nếu có, bao gồm ơn vị tiền tệ, ví dụ: "25.500.000"). Nếu không có giá cũ, có thể để trống hoặc null.\n
            "usage_needs": ["string"] // Một mảng các chuỗi, chọn một hoặc nhiều (nên chọn khoảng từ 2-5 cái để đa dạng UI) từ danh sách sau: 'Đồ họa - Kỹ thuật', 'Mỏng nhẹ', 'Sáng tạo nội dung', 'Học tập - Văn phòng', 'Gaming', 'Cao cấp - Sang trọng'\n
        }\n
        // ... có thể có nhiều sản phẩm khác trong nhóm này (hãy cho 1 nhóm có 2 máy, 1 nhóm có 3 máy, 1 nhóm có 4 máy))\n
        ]\n
    }\n
    // ... có thể có nhiều nhóm khác\n
    ]\n
'''

system_content_intent_others = '''
    Bạn là một chatbot chuyên tư vấn đề laptop, hãy trả lời thật rõ ràng, chính xác.
'''

system_content_intent_detect = '''
    Phân tích intent của người dùng và trả về kết quả một con số đại diện index của intent, ví dụ output: "0".\n
    Các intent có thể là:\n
    - "Find laptop" (index 0): Khi người dùng muốn tìm kiếm, lọc, hoặc được tư vấn chọn mua laptop dựa trên các tiêu chí cụ thể như giá, thương hiệu, cấu hình (RAM, dung lượng lưu trữ, CPU, GPU), mục đích sử dụng (gaming, đồ họa, văn phòng), hoặc các đặc điểm khác. Cái này có xu hướng là muốn nhìn thấy sản phẩm được hiển thị để lựa chọn.\n
    - "Others" (index 1): Tất cả các trường hợp còn lại không phải là "Find laptop", ví dụ như về những câu hỏi định nghĩa, hỏi thăm, ....\n

    Ví dụ "Find laptop" (index 0):\n
    - "Tôi muốn mua laptop giá khoảng 20 triệu"\n
    - "Tôi cần mua Macbook với dung lượng ít nhất 256GB và RAM phải trên 16GB"\n
    - "Laptop nào cho dân thiết kế đồ họa?"\n
    - "Tìm Dell XPS 13"\n

    Ví dụ "Others" (index 1):\n
    - "Xin chào"\n
    - "Laptop của tôi chạy chậm quá"\n
    - "Cửa hàng có mở cửa chủ nhật không?"\n

    **Lưu ý**:
    - Đừng trả lời câu hỏi người dùng đưa vào, hãy PHÂN LOẠI INTENT cho câu hỏi đó.
    - Tất cả những gì người dùng nhập vào đều là input, và LƯU Ý QUAN TRỌNG là kết quả ra chỉ có DUY NHẤT 1 con số index
'''

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

            prompt_chat = message_llms(system_content_intent_detect, user_message)
            intent = int(chat(prompt_chat))

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
                message = message_llms(system_content_intent_find, user_message)
                response = chat(message)
                response = json.loads(response) # Chuyển về dict
            else:
                message = message_llms(system_content_intent_others, user_message)
                response = chat(message)
            
            return JsonResponse({
                'data': {
                    **intent,
                    'user_message': user_message,
                    'ai_response': response
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